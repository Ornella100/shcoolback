from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Classe, Eleve, Inscription

from .models import AttendanceRecord, AttendanceSession


class AttendanceView(APIView):
    """Lit ou enregistre l'appel d'une classe pour une date précise."""

    permission_classes = [permissions.IsAuthenticated]

    def _classroom(self, request, classroom_id):
        if not request.user.school_id or not str(classroom_id or '').isdigit():
            return None
        return Classe.objects.filter(
            id=int(classroom_id), school_id=request.user.school_id,
        ).select_related('annee').first()

    def _date(self, value):
        if not isinstance(value, str):
            return None
        try:
            return parse_date(value)
        except ValueError:
            return None

    def get(self, request):
        classroom_id = request.query_params.get('classe')
        day = self._date(request.query_params.get('date'))
        if not classroom_id or not day:
            return Response(
                {'detail': 'Les paramètres classe et date (AAAA-MM-JJ) sont requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        classroom = self._classroom(request, classroom_id)
        if classroom is None:
            return Response({'detail': 'Classe introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        session = AttendanceSession.objects.filter(classroom=classroom, date=day).first()
        records = {
            record.student_id: record
            for record in (
                session.records.select_related('student').all() if session else []
            )
        }
        students = Eleve.objects.filter(
            school_id=request.user.school_id,
            is_active=True,
            inscriptions__annee=classroom.annee,
            inscriptions__classe=classroom,
            inscriptions__statut=Inscription.Statut.INSCRIT,
        ).distinct().order_by('last_name', 'first_name')

        return Response({
            'session_id': session.id if session else None,
            'classe': classroom.id,
            'classe_name': classroom.name,
            'date': day.isoformat(),
            'students': [
                {
                    'id': student.id,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'matricule': student.matricule,
                    'status': records[student.id].status if student.id in records else None,
                    'note': records[student.id].note if student.id in records else '',
                }
                for student in students
            ],
        })

    def post(self, request):
        classroom_id = request.data.get('classe')
        day = self._date(request.data.get('date'))
        entries = request.data.get('students')
        if not classroom_id or not day:
            return Response(
                {'detail': 'Les champs classe et date (AAAA-MM-JJ) sont requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not isinstance(entries, list):
            return Response(
                {'students': 'Une liste de présences est requise.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        classroom = self._classroom(request, classroom_id)
        if classroom is None:
            return Response({'detail': 'Classe introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        student_ids = [entry.get('id') for entry in entries if isinstance(entry, dict)]
        if (
            len(student_ids) != len(entries)
            or any(not isinstance(student_id, int) or isinstance(student_id, bool) or student_id < 1 for student_id in student_ids)
            or len(set(student_ids)) != len(student_ids)
        ):
            return Response(
                {'students': 'Chaque élève doit apparaître une seule fois avec un identifiant valide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_statuses = set(AttendanceRecord.Status.values)
        invalid = [
            entry.get('id') for entry in entries
            if entry.get('status') not in valid_statuses
        ]
        if invalid:
            return Response(
                {'students': f"Statut invalide pour l'élève {invalid[0]}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrolled_ids = set(Inscription.objects.filter(
            eleve_id__in=student_ids,
            eleve__school_id=request.user.school_id,
            eleve__is_active=True,
            annee=classroom.annee,
            classe=classroom,
            statut=Inscription.Statut.INSCRIT,
        ).values_list('eleve_id', flat=True))
        if enrolled_ids != set(student_ids):
            return Response(
                {'students': "Un ou plusieurs élèves ne sont pas inscrits dans cette classe pour l'année concernée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            session, _ = AttendanceSession.objects.get_or_create(
                school_id=request.user.school_id,
                classroom=classroom,
                date=day,
                defaults={'created_by': request.user},
            )
            for entry in entries:
                AttendanceRecord.objects.update_or_create(
                    session=session,
                    student_id=entry['id'],
                    defaults={
                        'status': entry['status'],
                        'note': str(entry.get('note') or '').strip()[:300],
                    },
                )

        return Response(
            {'session_id': session.id, 'saved': len(entries), 'date': day.isoformat()},
            status=status.HTTP_200_OK,
        )
