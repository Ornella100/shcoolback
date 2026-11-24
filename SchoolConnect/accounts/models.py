from django.contrib.auth.models import AbstractUser
from django.db import models

from schools.validators import phone_validator


class User(AbstractUser):
    class AccountType(models.TextChoices):
        STAFF = 'STAFF', 'Personnel'
        PARENT = 'PARENT', 'Parent'

    """Compte du personnel d'un établissement ou compte de portail parent.

    Les comptes STAFF représentent l'école et disposent de ses droits opérationnels.
    Les comptes PARENT sont rattachés à une fiche parent et n'accèdent qu'au portail
    parent, via ParentPortalAccessMiddleware.
    """

    school = models.ForeignKey(
        'schools.School',
        on_delete=models.PROTECT,
        related_name='staff',
        null=True,
        blank=True,
        help_text="Vide pour un compte AfriLab (superuser) non rattaché à une école.",
    )
    account_type = models.CharField(
        max_length=10, choices=AccountType.choices, default=AccountType.STAFF,
    )
    parent_profile = models.OneToOneField(
        'parents.Parent', on_delete=models.CASCADE, null=True, blank=True,
        related_name='portal_account',
    )
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])

    class Meta:
        ordering = ['school', 'last_name', 'first_name']

    def __str__(self):
        full_name = self.get_full_name() or self.username
        return f"{full_name} ({self.school})" if self.school else full_name
