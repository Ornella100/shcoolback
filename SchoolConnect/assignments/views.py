from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Eleve, Inscription

from .models import Assignment, AssignmentSubmission
from .serializers import AssignmentSerializer, AssignmentSubmissionSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.user.school_id
        if not school_id:
            return Assignment.objects.none()
        qs = Assignment.objects.filter(school_id=school_id).select_related(
            'annee', 'classroom', 'subject',
        )
        year_id = self.request.query_params.get('annee')
        classroom_id = self.request.query_params.get('classe')
        if year_id:
            qs = qs.filter(annee_id=year_id) if year_id.isdigit() else qs.none()
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id) if classroom_id.isdigit() else qs.none()
        return qs


class AssignmentSubmissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _assignment(self, request, assignment_id):
        return get_object_or_404(
            Assignment.objects.select_related('annee', 'classroom'),
            id=assignment_id,
            school_id=request.user.school_id,
        )

    def get(self, request, assignment_id):
        assignment = self._assignment(request, assignment_id)
        students = Eleve.objects.filter(
            school_id=request.user.school_id,
            is_active=True,
            inscriptions__annee=assignment.annee,
            inscriptions__classe=assignment.classroom,
            inscriptions__statut=Inscription.Statut.INSCRIT,
        ).distinct().order_by('last_name', 'first_name')
        records = {record.student_id: record for record in assignment.submissions.all()}
        return Response({
            'assignment': AssignmentSerializer(assignment).data,
            'students': [
                {
                    'id': student.id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'matricule': student.matricule,
                    'status': records[student.id].status if student.id in records else AssignmentSubmission.Status.PENDING,
                    'submitted_at': records[student.id].submitted_at if student.id in records else None,
                    'comment': records[student.id].comment if student.id in records else '',
                    'score': records[student.id].score if student.id in records else None,
                }
                for student in students
            ],
        })

    def put(self, request, assignment_id):
        assignment = self._assignment(request, assignment_id)
        entries = request.data.get('students')
        if not isinstance(entries, list):
            return Response({'students': 'Une liste de remises est requise.'}, status=status.HTTP_400_BAD_REQUEST)
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
            annee=assignment.annee,
            classe=assignment.classroom,
            statut=Inscription.Statut.INSCRIT,
        ).values_list('eleve_id', flat=True))
        if enrolled != set(student_ids):
            return Response({'students': "Un ou plusieurs élèves ne sont pas inscrits dans cette classe."}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = set(AssignmentSubmission.Status.values)
        validated_rows = []
        errors = {}
        for row in entries:
            serializer = AssignmentSubmissionSerializer(
                data={
                    'student': row['id'],
                    'status': row.get('status', AssignmentSubmission.Status.PENDING),
                    'comment': row.get('comment') or '',
                    'score': row.get('score'),
                },
                context={'assignment': assignment},
            )
            if not serializer.is_valid():
                errors[row['id']] = serializer.errors
                continue
            if serializer.validated_data['status'] not in valid_statuses:
                errors[row['id']] = {'status': 'Statut inconnu.'}
                continue
            validated_rows.append((row['id'], serializer.validated_data))
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for student_id, values in validated_rows:
                record, created = AssignmentSubmission.objects.get_or_create(
                    assignment=assignment,
                    student_id=student_id,
                    defaults={
                        'status': AssignmentSubmission.Status.PENDING,
                        'submitted_at': None,
                    },
                )
                record.status = values['status']
                record.comment = values['comment']
                record.score = values['score']
                if record.status == AssignmentSubmission.Status.PENDING:
                    record.submitted_at = None
                elif record.submitted_at is None:
                    record.submitted_at = timezone.now()
                record.save()
        return Response({'saved': len(validated_rows), 'assignment': assignment.id})
