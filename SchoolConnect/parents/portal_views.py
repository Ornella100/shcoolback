from django.db.models import Count
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from accounts.models import User
from academics import services as academics_services
from academics.models import Inscription
from assignments.models import Assignment, AssignmentSubmission
from attendance.models import AttendanceRecord
from messaging.models import MessageRecipient
from results.models import StudentScore


class ParentPortalOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.account_type == User.AccountType.PARENT
            and user.parent_profile_id
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, ParentPortalOnly])
def parent_portal_summary(request):
    parent = request.user.parent_profile
    school = parent.school
    year = academics_services.get_current_year(school)
    children = parent.students.filter(
        school=school,
        is_active=True,
    ).distinct().order_by('last_name', 'first_name')
    child_data = []

    for student in children:
        inscription = None
        if year:
            inscription = student.inscriptions.filter(
                annee=year,
                statut=Inscription.Statut.INSCRIT,
            ).select_related('classe').first()

        attendance = {
            key: 0 for key in AttendanceRecord.Status.values
        }
        grades = []
        assignments = []
        if year:
            attendance_rows = AttendanceRecord.objects.filter(
                student=student,
                session__school=school,
                session__classroom__annee=year,
            ).values('status').annotate(count=Count('id'))
            attendance.update({row['status']: row['count'] for row in attendance_rows})

            grades = [
                {
                    'assessment': score.assessment.title,
                    'subject': score.assessment.subject.name,
                    'date': score.assessment.date.isoformat(),
                    'score': str(score.score),
                    'max_score': str(score.assessment.max_score),
                }
                for score in StudentScore.objects.filter(
                    student=student,
                    assessment__school=school,
                    assessment__annee=year,
                    score__isnull=False,
                ).select_related('assessment__subject').order_by('-assessment__date')[:10]
            ]

            if inscription:
                assignment_rows = Assignment.objects.filter(
                    school=school,
                    annee=year,
                    classroom=inscription.classe,
                ).select_related('subject').order_by('due_date')[:20]
                submissions = {
                    record.assignment_id: record
                    for record in AssignmentSubmission.objects.filter(
                        assignment__in=assignment_rows,
                        student=student,
                    )
                }
                assignments = [
                    {
                        'id': assignment.id,
                        'title': assignment.title,
                        'subject': assignment.subject.name if assignment.subject_id else '',
                        'instructions': assignment.instructions,
                        'due_date': assignment.due_date.isoformat(),
                        'status': submissions[assignment.id].status if assignment.id in submissions else AssignmentSubmission.Status.PENDING,
                        'status_label': submissions[assignment.id].get_status_display() if assignment.id in submissions else AssignmentSubmission.Status.PENDING.label,
                        'comment': submissions[assignment.id].comment if assignment.id in submissions else '',
                        'score': str(submissions[assignment.id].score) if assignment.id in submissions and submissions[assignment.id].score is not None else None,
                        'max_score': str(assignment.max_score) if assignment.max_score is not None else None,
                    }
                    for assignment in assignment_rows
                ]

        child_data.append({
            'id': student.id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'matricule': student.matricule,
            'classroom': inscription.classe.name if inscription else '',
            'annee': year.label if year else '',
            'attendance': attendance,
            'recent_grades': grades,
            'assignments': assignments,
        })

    messages = MessageRecipient.objects.filter(
        parent=parent,
        message__school=school,
        message__sent_at__isnull=False,
        status=MessageRecipient.Status.ENVOYE,
    ).select_related('message').order_by('-message__sent_at')[:20]
    message_data = [
        {
            'id': item.id,
            'subject': item.message.subject or school.name,
            'body': item.rendered_body or item.message.body,
            'sent_at': item.sent_at.isoformat() if item.sent_at else item.message.sent_at.isoformat(),
            'channel': item.channel_used,
        }
        for item in messages
    ]

    return Response({
        'parent': {
            'first_name': parent.first_name,
            'last_name': parent.last_name,
            'school': school.name,
        },
        'annee': year.label if year else None,
        'children': child_data,
        'messages': message_data,
    })
