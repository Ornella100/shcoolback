from django.conf import settings
from django.db import models


class Incident(models.Model):
    class Category(models.TextChoices):
        BEHAVIOR = 'BEHAVIOR', 'Comportement'
        BULLYING = 'BULLYING', 'Harcèlement'
        HEALTH = 'HEALTH', 'Santé'
        PROPERTY = 'PROPERTY', 'Dégradation ou perte'
        OTHER = 'OTHER', 'Autre'

    class Severity(models.TextChoices):
        LOW = 'LOW', 'Faible'
        MEDIUM = 'MEDIUM', 'Moyenne'
        HIGH = 'HIGH', 'Élevée'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'En cours'
        RESOLVED = 'RESOLVED', 'Résolu'

    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='incidents',
    )
    annee = models.ForeignKey(
        'academics.AnneeScolaire', on_delete=models.CASCADE, related_name='incidents',
    )
    classroom = models.ForeignKey(
        'academics.Classe', on_delete=models.PROTECT, related_name='incidents',
    )
    student = models.ForeignKey(
        'academics.Eleve', on_delete=models.CASCADE, related_name='incidents',
    )
    date = models.DateField()
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    severity = models.CharField(max_length=6, choices=Severity.choices, default=Severity.LOW)
    description = models.TextField(max_length=3000)
    action_taken = models.TextField(max_length=2000, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(max_length=2000, blank=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reported_incidents',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['school', 'date']),
            models.Index(fields=['school', 'status']),
        ]

    def __str__(self):
        return f'{self.student} — {self.get_category_display()} ({self.date})'
