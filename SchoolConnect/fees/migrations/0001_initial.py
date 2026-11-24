import decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('academics', '0007_remove_classe_academic_year'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeeInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
                ('due_date', models.DateField()),
                ('status', models.CharField(choices=[('ISSUED', 'Émise'), ('CANCELLED', 'Annulée')], default='ISSUED', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annee', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fee_invoices', to='academics.anneescolaire')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fee_invoices', to='academics.classe')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_fee_invoices', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fee_invoices', to='schools.school')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fee_invoices', to='academics.eleve')),
            ],
            options={
                'ordering': ['due_date', 'student__last_name', 'student__first_name'],
            },
        ),
        migrations.CreateModel(
            name='FeePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
                ('method', models.CharField(choices=[('CASH', 'Espèces'), ('MOBILE_MONEY', 'Mobile money'), ('BANK_TRANSFER', 'Virement bancaire'), ('OTHER', 'Autre')], max_length=20)),
                ('reference', models.CharField(blank=True, max_length=100)),
                ('paid_at', models.DateField(default=django.utils.timezone.localdate)),
                ('note', models.CharField(blank=True, max_length=300)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='fees.feeinvoice')),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_fee_payments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-paid_at', '-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='feeinvoice',
            constraint=models.UniqueConstraint(fields=('school', 'annee', 'classroom', 'student', 'title'), name='uq_fee_student_title_year'),
        ),
    ]
