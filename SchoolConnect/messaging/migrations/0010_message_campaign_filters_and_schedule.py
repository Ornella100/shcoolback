from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('messaging', '0009_alter_messagerecipient_skip_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='message', name='scope_gender',
            field=models.CharField(blank=True, choices=[('M', 'Garçons'), ('F', 'Filles')], max_length=1),
        ),
        migrations.AddField(
            model_name='message', name='scope_attendance',
            field=models.CharField(blank=True, choices=[('ABSENT', 'Absents'), ('LATE', 'En retard')], max_length=10),
        ),
        migrations.AddField(
            model_name='message', name='scope_attendance_days',
            field=models.PositiveSmallIntegerField(default=7),
        ),
        migrations.AddField(
            model_name='message', name='scope_unpaid_only',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message', name='scheduled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message', name='queued_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='message', name='status',
            field=models.CharField(
                choices=[
                    ('BROUILLON', 'Brouillon'), ('PLANIFIE', 'Programmé'),
                    ('EN_ATTENTE', 'En attente'), ('EN_COURS', 'En cours'),
                    ('ENVOYE', 'Envoyé'), ('PARTIEL', 'Partiellement envoyé'),
                    ('ECHEC', 'Échec'), ('ANNULE', 'Annulé'),
                ], default='BROUILLON', max_length=10,
            ),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['status', 'scheduled_at'], name='msg_status_sched_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['status', 'queued_at'], name='msg_status_queue_idx'),
        ),
    ]
