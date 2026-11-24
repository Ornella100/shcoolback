from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Assignment(models.Model):
    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='assignments',
    )
    annee = models.ForeignKey(
        'academics.AnneeScolaire', on_delete=models.CASCADE, related_name='assignments',
    )
    classroom = models.ForeignKey(
        'academics.Classe', on_delete=models.CASCADE, related_name='assignments',
    )
    subject = models.ForeignKey(
        'results.Subject', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments',
    )
    title = models.CharField(max_length=180)
    instructions = models.TextField(max_length=5000, blank=True)
    assigned_date = models.DateField()
    due_date = models.DateField()
    max_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'title']

    def __str__(self):
        return f'{self.title} — {self.classroom.name}'


class AssignmentSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'À remettre'
        SUBMITTED = 'SUBMITTED', 'Remis'
        LATE = 'LATE', 'Remis en retard'
        REVIEWED = 'REVIEWED', 'Corrigé'

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, related_name='submissions',
    )
    student = models.ForeignKey(
        'academics.Eleve', on_delete=models.CASCADE, related_name='assignment_submissions',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(null=True, blank=True)
    comment = models.CharField(max_length=1000, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__last_name', 'student__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'student'], name='unique_submission_per_assignment_student',
            ),
        ]

    def __str__(self):
        return f'{self.student} — {self.assignment.title}'
