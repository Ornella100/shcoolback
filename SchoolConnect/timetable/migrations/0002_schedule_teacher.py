from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('teachers', '0001_initial'),
        ('timetable', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduleslot',
            name='teacher',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='schedule_slots',
                to='teachers.teacher',
            ),
        ),
    ]
