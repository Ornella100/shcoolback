import csv
from collections import defaultdict
from decimal import Decimal

from django.db.models import Count
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from academics import services as academics_services
from academics.models import Classe, Inscription
from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from discipline.models import Incident
from results.models import StudentScore


ATTENDANCE_STATUSES = AttendanceRecord.Status.values


def _build_school_report(request):
    user = request.user
    if not user.school_id or user.account_type != 'STAFF':
        return None, Response(
            {'detail': "Ce rapport est réservé au personnel d'un établissement."},
            status=status.HTTP_403_FORBIDDEN,
        )
    year_id = request.query_params.get('annee')
    if year_id and not year_id.isdigit():
        return None, Response({'annee': 'Identifiant d’année invalide.'}, status=status.HTTP_400_BAD_REQUEST)
    year = academics_services.resolve_annee(user.school, year_id)
    if year is None:
        message = (
            "L'année demandée n'appartient pas à votre établissement."
            if year_id else "Aucune année scolaire en cours. Créez une année ou sélectionnez-en une."
        )
        return None, Response({'annee': message}, status=status.HTTP_400_BAD_REQUEST)

    school = user.school
    classes = list(Classe.objects.filter(
        school=school,
        annee=year,
    ).order_by('level', 'name'))
    class_ids = [classroom.id for classroom in classes]
    enrollment_counts = {
        row['classe_id']: row['total']
        for row in Inscription.objects.filter(
            classe_id__in=class_ids,
            annee=year,
            statut=Inscription.Statut.INSCRIT,
        ).order_by().values('classe_id').annotate(total=Count('eleve_id', distinct=True))
    }

    attendance = defaultdict(lambda: {key: 0 for key in ATTENDANCE_STATUSES})
    attendance_months = defaultdict(lambda: {key: 0 for key in ATTENDANCE_STATUSES})
    attendance_rows = AttendanceRecord.objects.filter(
        session__school=school,
        session__classroom__in=classes,
    ).order_by().values('session__classroom_id', 'session__date', 'status').annotate(total=Count('id'))
    for row in attendance_rows:
        class_id = row['session__classroom_id']
        attendance[class_id][row['status']] += row['total']
        month = row['session__date'].strftime('%Y-%m')
        attendance_months[month][row['status']] += row['total']

    score_weighted = defaultdict(lambda: Decimal('0'))
    score_weights = defaultdict(lambda: Decimal('0'))
    grade_rows = StudentScore.objects.filter(
        assessment__school=school,
        assessment__annee=year,
        score__isnull=False,
    ).select_related('assessment__subject')
    for score in grade_rows:
        assessment = score.assessment
        weight = assessment.coefficient * assessment.subject.coefficient
        normalized = score.score * Decimal('20') / assessment.max_score
        score_weighted[assessment.classroom_id] += normalized * weight
        score_weights[assessment.classroom_id] += weight

    assignments = defaultdict(int)
    for row in Assignment.objects.filter(
        school=school, annee=year, classroom_id__in=class_ids,
    ).order_by().values('classroom_id').annotate(total=Count('id')):
        assignments[row['classroom_id']] = row['total']

    submitted = defaultdict(int)
    for row in AssignmentSubmission.objects.filter(
        assignment__school=school,
        assignment__annee=year,
        assignment__classroom_id__in=class_ids,
    ).exclude(status=AssignmentSubmission.Status.PENDING).order_by().values(
        'assignment__classroom_id',
    ).annotate(total=Count('id')):
        submitted[row['assignment__classroom_id']] = row['total']

    incidents = defaultdict(lambda: {'total': 0, 'open': 0})
    for row in Incident.objects.filter(
        school=school, annee=year, classroom_id__in=class_ids,
    ).order_by().values('classroom_id', 'status').annotate(total=Count('id')):
        incidents[row['classroom_id']]['total'] += row['total']
        if row['status'] == Incident.Status.OPEN:
            incidents[row['classroom_id']]['open'] += row['total']

    class_rows = []
    for classroom in classes:
        class_id = classroom.id
        counts = attendance[class_id]
        marked = sum(counts.values())
        present = counts[AttendanceRecord.Status.PRESENT]
        late = counts[AttendanceRecord.Status.LATE]
        attendance_rate = round((present + late) * 100 / marked, 2) if marked else None
        students_count = enrollment_counts.get(class_id, 0)
        possible_submissions = assignments[class_id] * students_count
        avg = (
            (score_weighted[class_id] / score_weights[class_id]).quantize(Decimal('0.01'))
            if score_weights[class_id] else None
        )
        class_rows.append({
            'classe': classroom.id,
            'classe_name': classroom.name,
            'level': classroom.level,
            'students': students_count,
            'attendance': {
                'marked': marked,
                'present': present,
                'absent': counts[AttendanceRecord.Status.ABSENT],
                'late': late,
                'excused': counts[AttendanceRecord.Status.EXCUSED],
                'rate': attendance_rate,
            },
            'average_out_of_20': str(avg) if avg is not None else None,
            'assignments': {
                'total': assignments[class_id],
                'submitted': submitted[class_id],
                'expected_submissions': possible_submissions,
                'rate': round(submitted[class_id] * 100 / possible_submissions, 2) if possible_submissions else None,
            },
            'incidents': incidents[class_id],
        })

    total_marked = sum(row['attendance']['marked'] for row in class_rows)
    total_present_late = sum(
        row['attendance']['present'] + row['attendance']['late'] for row in class_rows
    )
    total_students = sum(row['students'] for row in class_rows)
    total_grades_weighted = sum(score_weighted.values(), Decimal('0'))
    total_grade_weights = sum(score_weights.values(), Decimal('0'))
    possible = sum(row['assignments']['expected_submissions'] for row in class_rows)
    total_submitted = sum(row['assignments']['submitted'] for row in class_rows)

    return {
        'annee': year.id,
        'annee_label': year.label,
        'generated_at': timezone.now().isoformat(),
        'summary': {
            'classes': len(classes),
            'students': total_students,
            'attendance_rate': round(total_present_late * 100 / total_marked, 2) if total_marked else None,
            'attendance_marked': total_marked,
            'average_out_of_20': str((total_grades_weighted / total_grade_weights).quantize(Decimal('0.01'))) if total_grade_weights else None,
            'assignment_submission_rate': round(total_submitted * 100 / possible, 2) if possible else None,
            'open_incidents': sum(row['incidents']['open'] for row in class_rows),
        },
        'monthly_attendance': [
            {
                'month': month,
                'marked': sum(counts.values()),
                'present': counts[AttendanceRecord.Status.PRESENT],
                'absent': counts[AttendanceRecord.Status.ABSENT],
                'late': counts[AttendanceRecord.Status.LATE],
                'excused': counts[AttendanceRecord.Status.EXCUSED],
            }
            for month, counts in sorted(attendance_months.items())
        ],
        'classes': class_rows,
    }, None


class SchoolReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        report, error = _build_school_report(request)
        if error:
            return error
        return Response(report)


class SchoolReportExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        report, error = _build_school_report(request)
        if error:
            return error
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response.write('\ufeff')
        response['Content-Disposition'] = (
            f'attachment; filename="rapport_scolaire_{report["annee_label"]}.csv"'
        )
        writer = csv.writer(response, delimiter=';')
        writer.writerow([
            'Classe', 'Niveau', 'Élèves inscrits', 'Appels renseignés',
            'Taux de présence (%)', 'Moyenne / 20', 'Devoirs',
            'Remises attendues', 'Remises enregistrées', 'Taux de remise (%)',
            'Incidents', 'Incidents ouverts',
        ])
        for row in report['classes']:
            writer.writerow([
                row['classe_name'],
                row['level'],
                row['students'],
                row['attendance']['marked'],
                row['attendance']['rate'] if row['attendance']['rate'] is not None else '',
                row['average_out_of_20'] or '',
                row['assignments']['total'],
                row['assignments']['expected_submissions'],
                row['assignments']['submitted'],
                row['assignments']['rate'] if row['assignments']['rate'] is not None else '',
                row['incidents']['total'],
                row['incidents']['open'],
            ])
        return response
