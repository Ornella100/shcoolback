from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Subject(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    coefficient = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['school', 'name'], name='unique_subject_name_per_school'),
        ]

    def __str__(self):
        return self.name


class Assessment(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='assessments')
    annee = models.ForeignKey(
        'academics.AnneeScolaire', on_delete=models.CASCADE, related_name='assessments',
    )
    classroom = models.ForeignKey(
        'academics.Classe', on_delete=models.CASCADE, related_name='assessments',
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name='assessments')
    title = models.CharField(max_length=150)
    date = models.DateField()
    max_score = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('20.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    coefficient = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_assessments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'subject__name', 'title']

    def __str__(self):
        return f'{self.title} — {self.classroom.name}'


class StudentScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey(
        'academics.Eleve', on_delete=models.CASCADE, related_name='assessment_scores',
    )
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    appreciation = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['student__last_name', 'student__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['assessment', 'student'], name='unique_score_per_assessment_student',
            ),
        ]

    def __str__(self):
        return f'{self.student} — {self.assessment.title}'
