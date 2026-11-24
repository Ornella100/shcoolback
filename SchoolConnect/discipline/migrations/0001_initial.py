import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('academics', '0007_remove_classe_academic_year'),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Incident',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('category', models.CharField(choices=[('BEHAVIOR', 'Comportement'), ('BULLYING', 'Harcèlement'), ('HEALTH', 'Santé'), ('PROPERTY', 'Dégradation ou perte'), ('OTHER', 'Autre')], default='OTHER', max_length=12)),
                ('severity', models.CharField(choices=[('LOW', 'Faible'), ('MEDIUM', 'Moyenne'), ('HIGH', 'Élevée')], default='LOW', max_length=6)),
                ('description', models.TextField(max_length=3000)),
                ('action_taken', models.TextField(blank=True, max_length=2000)),
                ('status', models.CharField(choices=[('OPEN', 'En cours'), ('RESOLVED', 'Résolu')], default='OPEN', max_length=10)),
                ('resolution', models.TextField(blank=True, max_length=2000)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='academics.anneescolaire')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='incidents', to='academics.classe')),
                ('reported_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_incidents', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='schools.school')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incidents', to='academics.eleve')),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['school', 'date'], name='discipline__school__607971_idx'),
        ),
        migrations.AddIndex(
            model_name='incident',
            index=models.Index(fields=['school', 'status'], name='discipline__school__faf066_idx'),
        ),
    ]
