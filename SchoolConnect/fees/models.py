from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class FeeInvoice(models.Model):
    class Status(models.TextChoices):
        ISSUED = 'ISSUED', 'Émise'
        CANCELLED = 'CANCELLED', 'Annulée'

    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='fee_invoices')
    annee = models.ForeignKey('academics.AnneeScolaire', on_delete=models.PROTECT, related_name='fee_invoices')
    classroom = models.ForeignKey('academics.Classe', on_delete=models.PROTECT, related_name='fee_invoices')
    student = models.ForeignKey('academics.Eleve', on_delete=models.PROTECT, related_name='fee_invoices')
    title = models.CharField(max_length=120)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ISSUED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_fee_invoices',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'student__last_name', 'student__first_name']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'annee', 'classroom', 'student', 'title'],
                name='uq_fee_student_title_year',
            ),
        ]

    def __str__(self):
        return f'{self.title} — {self.student}'


class FeePayment(models.Model):
    class Method(models.TextChoices):
        CASH = 'CASH', 'Espèces'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile money'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Virement bancaire'
        OTHER = 'OTHER', 'Autre'

    invoice = models.ForeignKey(FeeInvoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateField(default=timezone.localdate)
    note = models.CharField(max_length=300, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='recorded_fee_payments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-paid_at', '-created_at']

    def __str__(self):
        return f'{self.amount} — {self.invoice}'
