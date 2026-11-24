import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_remove_user_role'),
        ('parents', '0002_parent_school'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='account_type',
            field=models.CharField(
                choices=[('STAFF', 'Personnel'), ('PARENT', 'Parent')],
                default='STAFF',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='parent_profile',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='portal_account',
                to='parents.parent',
            ),
        ),
    ]
