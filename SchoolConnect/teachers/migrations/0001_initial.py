from django.db import migrations, models
import django.db.models.deletion
import schools.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('results', '0001_initial'),
        ('schools', '0002_school_email_monthly_limit_school_quota_reset_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=100, verbose_name='prénom')),
                ('last_name', models.CharField(max_length=100, verbose_name='nom')),
                ('phone_number', models.CharField(blank=True, max_length=20, validators=[schools.validators.phone_validator], verbose_name='téléphone')),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('specialty', models.CharField(blank=True, max_length=100, verbose_name='spécialité')),
                ('hire_date', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='schools.school')),
                ('subjects', models.ManyToManyField(blank=True, related_name='teachers', to='results.subject')),
            ],
            options={'ordering': ['last_name', 'first_name']},
        ),
        migrations.AddIndex(
            model_name='teacher',
            index=models.Index(fields=['school', 'last_name', 'first_name'], name='teacher_school_name_idx'),
        ),
    ]
