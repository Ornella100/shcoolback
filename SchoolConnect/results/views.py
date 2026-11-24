from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import AnneeScolaire, Classe, Eleve, Inscription

from .models import Assessment, StudentScore, Subject
from .serializers import AssessmentSerializer, StudentScoreSerializer, SubjectSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.school_id:
            return Subject.objects.none()
        return Subject.objects.filter(school_id=self.request.user.school_id)

    def perform_create(self, serializer):
        if not self.request.user.school_id:
            raise ValidationError('Ce compte doit être rattaché à une école.')
        serializer.save(school_id=self.request.user.school_id)


class AssessmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.school_id:
            return Assessment.objects.none()
        qs = Assessment.objects.filter(
            school_id=self.request.user.school_id,
        ).select_related('annee', 'classroom', 'subject')
        classroom_id = self.request.query_params.get('classe')
        annee_id = self.request.query_params.get('annee')
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        if annee_id:
            qs = qs.filter(annee_id=annee_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class AssessmentGradesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _assessment(self, request, assessment_id):
        return get_object_or_404(
            Assessment.objects.select_related('classroom', 'annee'),
            id=assessment_id,
            school_id=request.user.school_id,
        )

    def get(self, request, assessment_id):
        assessment = self._assessment(request, assessment_id)
        students = Eleve.objects.filter(
            school_id=request.user.school_id,
            is_active=True,
            inscriptions__annee=assessment.annee,
            inscriptions__classe=assessment.classroom,
            inscriptions__statut=Inscription.Statut.INSCRIT,
        ).distinct().order_by('last_name', 'first_name')
        saved = {
            score.student_id: score
            for score in assessment.scores.all()
        }
        return Response({
            'assessment': AssessmentSerializer(assessment).data,
            'students': [
                {
                    'id': student.id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'matricule': student.matricule,
                    'score': saved[student.id].score if student.id in saved else None,
                    'appreciation': saved[student.id].appreciation if student.id in saved else '',
                }
                for student in students
            ],
        })

    def put(self, request, assessment_id):
        assessment = self._assessment(request, assessment_id)
        entries = request.data.get('students')
        if not isinstance(entries, list):
            return Response({'students': 'Une liste de notes est requise.'}, status=status.HTTP_400_BAD_REQUEST)
        student_ids = [row.get('id') for row in entries if isinstance(row, dict)]
        if (
            len(student_ids) != len(entries)
            or any(not isinstance(pk, int) or isinstance(pk, bool) or pk < 1 for pk in student_ids)
            or len(set(student_ids)) != len(student_ids)
        ):
            return Response({'students': 'Chaque élève doit apparaître une seule fois avec un identifiant valide.'}, status=status.HTTP_400_BAD_REQUEST)
        enrolled = set(Inscription.objects.filter(
            eleve_id__in=student_ids,
            eleve__school_id=request.user.school_id,
            eleve__is_active=True,
            annee=assessment.annee,
            classe=assessment.classroom,
            statut=Inscription.Statut.INSCRIT,
        ).values_list('eleve_id', flat=True))
        if enrolled != set(student_ids):
            return Response({'students': "Un ou plusieurs élèves ne sont pas inscrits dans cette classe."}, status=status.HTTP_400_BAD_REQUEST)

        validated_rows = []
        errors = {}
        for row in entries:
            serializer = StudentScoreSerializer(
                data={
                    'student': row['id'],
                    'score': row.get('score'),
                    'appreciation': row.get('appreciation') or '',
                },
                context={'assessment': assessment},
            )
            if not serializer.is_valid():
                errors[row['id']] = serializer.errors
            else:
                validated_rows.append((row['id'], serializer.validated_data))
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for student_id, values in validated_rows:
                score, _ = StudentScore.objects.update_or_create(
                    assessment=assessment,
                    student_id=student_id,
                    defaults={
                        'score': values['score'],
                        'appreciation': values['appreciation'],
                    },
                )
        return Response({'saved': len(validated_rows), 'assessment': assessment.id})


class BulletinView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.school_id:
            return Response({'detail': 'Ce compte doit être rattaché à une école.'}, status=status.HTTP_403_FORBIDDEN)
        classroom_id = request.query_params.get('classe')
        year_id = request.query_params.get('annee')
        if not classroom_id:
            return Response({'detail': 'Le paramètre classe est requis.'}, status=status.HTTP_400_BAD_REQUEST)
        classroom = get_object_or_404(
            Classe.objects.select_related('annee'),
            id=classroom_id,
            school_id=request.user.school_id,
        )
        year = classroom.annee
        if year_id:
            year = get_object_or_404(
                AnneeScolaire, id=year_id, school_id=request.user.school_id,
            )
            if classroom.annee_id != year.id:
                return Response({'detail': "Cette classe n'appartient pas à l'année choisie."}, status=status.HTTP_400_BAD_REQUEST)

        students = list(Eleve.objects.filter(
            school_id=request.user.school_id,
            is_active=True,
            inscriptions__annee=year,
            inscriptions__classe=classroom,
            inscriptions__statut=Inscription.Statut.INSCRIT,
        ).distinct().order_by('last_name', 'first_name'))
        assessments = Assessment.objects.filter(
            school_id=request.user.school_id,
            classroom=classroom,
            annee=year,
        ).select_related('subject').order_by('date', 'title')
        scores = StudentScore.objects.filter(
            assessment__in=assessments,
            student__in=students,
            score__isnull=False,
        ).select_related('assessment__subject')
        by_student = defaultdict(lambda: defaultdict(list))
        subjects_by_id = {assessment.subject_id: assessment.subject for assessment in assessments}
        for score in scores:
            assessment = score.assessment
            normalized = score.score * Decimal('20') / assessment.max_score
            by_student[score.student_id][assessment.subject_id].append({
                'title': assessment.title,
                'date': assessment.date.isoformat(),
                'score': str(score.score),
                'max_score': str(assessment.max_score),
                'score_out_of_20': normalized.quantize(Decimal('0.01')),
                'coefficient': assessment.coefficient,
            })

        bulletins = []
        for student in students:
            subjects = []
            total_weighted = Decimal('0')
            total_weight = Decimal('0')
            for subject in subjects_by_id.values():
                items = by_student[student.id].get(subject.id, [])
                weight = sum((item['coefficient'] for item in items), Decimal('0'))
                average = (
                    sum((item['score_out_of_20'] * item['coefficient'] for item in items), Decimal('0')) / weight
                    if weight else None
                )
                if average is not None:
                    total_weighted += average * subject.coefficient
                    total_weight += subject.coefficient
                subjects.append({
                    'id': subject.id,
                    'name': subject.name,
                    'coefficient': str(subject.coefficient),
                    'average_out_of_20': str(average.quantize(Decimal('0.01'))) if average is not None else None,
                    'assessments': [
                        {
                            **item,
                            'score_out_of_20': str(item['score_out_of_20']),
                            'coefficient': str(item['coefficient']),
                        }
                        for item in items
                    ],
                })
            bulletins.append({
                'student': student.id,
                'first_name': student.first_name,
                'last_name': student.last_name,
                'matricule': student.matricule,
                'subjects': subjects,
                'average_out_of_20': str((total_weighted / total_weight).quantize(Decimal('0.01'))) if total_weight else None,
            })
        return Response({
            'classe': classroom.id,
            'classe_name': classroom.name,
            'annee': year.id,
            'annee_label': year.label,
            'students': bulletins,
        })
