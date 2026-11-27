from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from hashlib import sha256
from base64 import urlsafe_b64encode


def encrypt_whatsapp_token(token):
    key = urlsafe_b64encode(sha256(settings.SECRET_KEY.encode('utf-8')).digest())
    return Fernet(key).encrypt(token.encode('utf-8')).decode('ascii')


def decrypt_whatsapp_token(value):
    if not value:
        return ''
    key = urlsafe_b64encode(sha256(settings.SECRET_KEY.encode('utf-8')).digest())
    return Fernet(key).decrypt(value.encode('ascii')).decode('utf-8')

from .validators import phone_validator


class School(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, validators=[phone_validator])
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    # Plafonds d'envoi mensuels par canal, fixés par AfriLab (jamais par l'école elle-même).
    # Vide = illimité. Voir messaging.services.quota_remaining() pour le calcul de la
    # fenêtre glissante : mois calendaire, sauf réinitialisation manuelle plus récente.
    sms_monthly_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text='Nombre de SMS envoyables ce mois. Vide = illimité.',
    )
    whatsapp_monthly_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text='Nombre de messages WhatsApp envoyables ce mois. Vide = illimité.',
    )
    email_monthly_limit = models.PositiveIntegerField(
        null=True, blank=True, help_text='Nombre d\'emails envoyables ce mois. Vide = illimité.',
    )
    quota_reset_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Dernière réinitialisation manuelle des compteurs. Vide = seul le "
                  'changement de mois calendaire remet les compteurs à zéro.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolWhatsAppConnection(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name='whatsapp_connection')
    phone_number_id = models.CharField(max_length=100)
    encrypted_access_token = models.TextField()
    api_version = models.CharField(max_length=20, default='v22.0')
    updated_at = models.DateTimeField(auto_now=True)

    def set_access_token(self, token):
        self.encrypted_access_token = encrypt_whatsapp_token(token)

    def get_access_token(self):
        return decrypt_whatsapp_token(self.encrypted_access_token)
