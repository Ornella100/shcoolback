from django.conf import settings
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
            name='AttendanceSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_sessions', to='academics.classe')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attendance_sessions', to=settings.AUTH_USER_MODEL)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_sessions', to='schools.school')),
            ],
            options={
                'ordering': ['-date', 'classroom__name'],
            },
        ),
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PRESENT', 'Présent'), ('ABSENT', 'Absent'), ('LATE', 'En retard'), ('EXCUSED', 'Absence justifiée')], max_length=10)),
                ('note', models.CharField(blank=True, max_length=300)),
                ('marked_at', models.DateTimeField(auto_now=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='attendance.attendancesession')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendance_records', to='academics.eleve')),
            ],
            options={
                'ordering': ['student__last_name', 'student__first_name'],
            },
        ),
        migrations.AddConstraint(
            model_name='attendancesession',
            constraint=models.UniqueConstraint(fields=('classroom', 'date'), name='unique_attendance_class_date'),
        ),
        migrations.AddIndex(
            model_name='attendancesession',
            index=models.Index(fields=['school', 'date'], name='attendance__school__3b5e5b_idx'),
        ),
        migrations.AddConstraint(
            model_name='attendancerecord',
            constraint=models.UniqueConstraint(fields=('session', 'student'), name='unique_attendance_student_session'),
        ),
    ]
