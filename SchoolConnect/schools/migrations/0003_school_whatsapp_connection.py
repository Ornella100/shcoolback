import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more')]

    operations = [
        migrations.CreateModel(
            name='SchoolWhatsAppConnection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number_id', models.CharField(max_length=100)),
                ('encrypted_access_token', models.TextField()),
                ('api_version', models.CharField(default='v22.0', max_length=20)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='whatsapp_connection', to='schools.school')),
            ],
        ),
    ]
