from django.conf import settings
from django.db import models


class AttendanceSession(models.Model):
    """Feuille d'appel d'une classe à une date donnée."""

    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='attendance_sessions',
    )
    classroom = models.ForeignKey(
        'academics.Classe', on_delete=models.CASCADE, related_name='attendance_sessions',
    )
    date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='attendance_sessions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'classroom__name']
        constraints = [
            models.UniqueConstraint(
                fields=['classroom', 'date'], name='unique_attendance_class_date',
            ),
        ]
        indexes = [models.Index(fields=['school', 'date'])]

    def __str__(self):
        return f'{self.classroom.name} — {self.date}'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Présent'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'En retard'
        EXCUSED = 'EXCUSED', 'Absence justifiée'

    session = models.ForeignKey(
        AttendanceSession, on_delete=models.CASCADE, related_name='records',
    )
    student = models.ForeignKey(
        'academics.Eleve', on_delete=models.CASCADE, related_name='attendance_records',
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    note = models.CharField(max_length=300, blank=True)
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__last_name', 'student__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'student'], name='unique_attendance_student_session',
            ),
        ]

    def __str__(self):
        return f'{self.student} — {self.get_status_display()}'
