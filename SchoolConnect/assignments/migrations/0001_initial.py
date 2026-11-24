import decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('academics', '0007_remove_classe_academic_year'),
        ('results', '0001_initial'),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Assignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('instructions', models.TextField(blank=True, max_length=5000)),
                ('assigned_date', models.DateField()),
                ('due_date', models.DateField()),
                ('max_score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='academics.anneescolaire')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='academics.classe')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_assignments', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='schools.school')),
                ('subject', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assignments', to='results.subject')),
            ],
            options={
                'ordering': ['due_date', 'title'],
            },
        ),
        migrations.CreateModel(
            name='AssignmentSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'À remettre'), ('SUBMITTED', 'Remis'), ('LATE', 'Remis en retard'), ('REVIEWED', 'Corrigé')], default='PENDING', max_length=10)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('comment', models.CharField(blank=True, max_length=1000)),
                ('score', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assignment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='assignments.assignment')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignment_submissions', to='academics.eleve')),
            ],
            options={
                'ordering': ['student__last_name', 'student__first_name'],
            },
        ),
        migrations.AddConstraint(
            model_name='assignmentsubmission',
            constraint=models.UniqueConstraint(fields=('assignment', 'student'), name='unique_submission_per_assignment_student'),
        ),
    ]
