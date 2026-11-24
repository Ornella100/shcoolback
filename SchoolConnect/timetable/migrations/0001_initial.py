from django.db import migrations, models
from django.db.models import F, Q
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('academics', '0007_remove_classe_academic_year'),
        ('results', '0001_initial'),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0, 'Lundi'), (1, 'Mardi'), (2, 'Mercredi'), (3, 'Jeudi'), (4, 'Vendredi'), (5, 'Samedi'), (6, 'Dimanche')])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('teacher_name', models.CharField(blank=True, max_length=120)),
                ('room', models.CharField(blank=True, max_length=80)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('annee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_slots', to='academics.anneescolaire')),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_slots', to='academics.classe')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_slots', to='schools.school')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='schedule_slots', to='results.subject')),
            ],
            options={
                'ordering': ['weekday', 'start_time', 'classroom__name'],
            },
        ),
        migrations.AddConstraint(
            model_name='scheduleslot',
            constraint=models.CheckConstraint(condition=Q(('end_time__gt', F('start_time'))), name='schedule_end_after_start'),
        ),
    ]
