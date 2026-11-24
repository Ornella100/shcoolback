import decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('academics', '0007_remove_classe_academic_year'),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('coefficient', models.DecimalField(decimal_places=2, default=decimal.Decimal('1.00'), max_digits=4, validators=[MinValueValidator(decimal.Decimal('0.01'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subjects', to='schools.school')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Assessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('date', models.DateField()),
                ('max_score', models.DecimalField(decimal_places=2, default=decimal.Decimal('20.00'), max_digits=6, validators=[MinValueValidator(decimal.Decimal('0.01'))])),
                ('coefficient', models.DecimalField(decimal_places=2, default=decimal.Decimal('1.00'), max_digits=4, validators=[MinValueValidator(decimal.Decimal('0.01'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('annee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessments', to='academics.anneescolaire')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessments', to='academics.classe')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_assessments', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessments', to='schools.school')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='assessments', to='results.subject')),
            ],
            options={
                'ordering': ['-date', 'subject__name', 'title'],
            },
        ),
        migrations.CreateModel(
            name='StudentScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('appreciation', models.CharField(blank=True, max_length=300)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='results.assessment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessment_scores', to='academics.eleve')),
            ],
            options={
                'ordering': ['student__last_name', 'student__first_name'],
            },
        ),
        migrations.AddConstraint(
            model_name='subject',
            constraint=models.UniqueConstraint(fields=('school', 'name'), name='unique_subject_name_per_school'),
        ),
        migrations.AddConstraint(
            model_name='studentscore',
            constraint=models.UniqueConstraint(fields=('assessment', 'student'), name='unique_score_per_assessment_student'),
        ),
    ]
