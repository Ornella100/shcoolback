import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SmsProvider:
    """Interface d'un fournisseur SMS réel. Implémenter `send()` suffit à brancher un
    vrai gateway (ex. SMSPro Africa) sans toucher au reste de `messaging/services.py`."""

    def send(self, contact, body):
        raise NotImplementedError


class SimulatedSmsProvider(SmsProvider):
    """Simulation héritée : ne contacte aucun fournisseur, répond toujours succès."""

    def send(self, contact, body):
        return True, ''


class EsmsAfricaProvider(SmsProvider):
    """Client du point d'envoi SMS eSMS Africa. La clé reste en variable d'environnement."""

    endpoint = 'https://sms.esmsafrica.io/api/messages/send'

    def __init__(self, api_key, sender_id='', timeout=15):
        self.api_key = api_key
        self.sender_id = sender_id
        self.timeout = timeout

    def send(self, contact, body):
        payload = {'to': contact, 'text': body}
        if self.sender_id:
            payload['sender_id'] = self.sender_id

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception('Échec réseau lors de l’envoi SMS eSMS Africa')
            return False, 'Le fournisseur SMS est momentanément injoignable'

        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.ok:
            return True, ''

        # Ne pas renvoyer de détail fourni par le gateway à l’interface : il peut
        # contenir des données techniques ou personnelles.
        error = result.get('error', {}) if isinstance(result, dict) else {}
        code = error.get('code') if isinstance(error, dict) else None
        logger.warning('eSMS Africa a refusé un SMS (HTTP %s, code %s)', response.status_code, code)
        if response.status_code == 402:
            return False, 'Solde eSMS Africa insuffisant'
        if response.status_code in (401, 403):
            return False, 'La clé API ou le sender ID eSMS Africa est refusé'
        return False, 'eSMS Africa a refusé le message (HTTP %s)' % response.status_code


class TextBeeProvider(SmsProvider):
    """Envoie un SMS via le téléphone Android associé au compte TextBee."""

    endpoint = 'https://api.textbee.dev/api/v1/gateway/send-sms'

    def __init__(self, api_key, device_id='', timeout=15):
        self.api_key = api_key
        self.device_id = device_id
        self.timeout = timeout

    def send(self, contact, body):
        payload = {'recipients': [contact], 'message': body}
        if self.device_id:
            payload['deviceId'] = self.device_id
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers={'x-api-key': self.api_key},
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception('Échec réseau lors de l’envoi SMS TextBee')
            return False, 'Le fournisseur SMS est momentanément injoignable'

        if response.ok:
            return True, ''

        logger.warning('TextBee a refusé un SMS (HTTP %s)', response.status_code)
        if response.status_code == 429:
            return False, 'La limite quotidienne ou mensuelle TextBee est atteinte'
        if response.status_code == 401:
            return False, 'La clé API TextBee est invalide ou révoquée'
        if response.status_code == 403:
            return False, 'Le compte TextBee ne peut pas envoyer de SMS'
        if response.status_code == 400:
            return False, 'Aucun téléphone TextBee actif ou autorisation SMS manquante'
        return False, 'TextBee a refusé le message (HTTP %s)' % response.status_code


class WhatsAppCloudProvider(SmsProvider):
    """Envoie des messages texte via WhatsApp Business Cloud API de Meta."""

    def __init__(self, access_token, phone_number_id, api_version='v22.0', timeout=15):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.timeout = timeout

    def send(self, contact, body):
        # Cloud API attend le numéro international sans le signe +.
        recipient = ''.join(ch for ch in contact if ch.isdigit())
        if not recipient:
            return False, 'Numéro WhatsApp invalide'
        endpoint = (
            f'https://graph.facebook.com/{self.api_version}/'
            f'{self.phone_number_id}/messages'
        )
        try:
            response = requests.post(
                endpoint,
                json={
                    'messaging_product': 'whatsapp',
                    'recipient_type': 'individual',
                    'to': recipient,
                    'type': 'text',
                    'text': {'preview_url': False, 'body': body},
                },
                headers={'Authorization': f'Bearer {self.access_token}'},
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception('Échec réseau lors de l’envoi WhatsApp Cloud')
            return False, 'Le fournisseur WhatsApp est momentanément injoignable'

        if response.ok:
            return True, ''
        try:
            payload = response.json()
            code = payload.get('error', {}).get('code')
        except (ValueError, AttributeError):
            code = None
        logger.warning('WhatsApp Cloud a refusé un message (HTTP %s, code %s)', response.status_code, code)
        if response.status_code in (401, 403):
            return False, 'Le jeton WhatsApp ou les permissions Meta sont refusés'
        if code == 131047:
            return False, 'Hors fenêtre de service : utilisez un modèle WhatsApp approuvé par Meta'
        return False, 'WhatsApp Cloud a refusé le message (HTTP %s)' % response.status_code


def get_sms_provider():
    """Fournisseur SMS configuré, ou simulation explicite pour le développement."""
    textbee_api_key = getattr(settings, 'TEXTBEE_API_KEY', '').strip()
    if textbee_api_key:
        return TextBeeProvider(
            api_key=textbee_api_key,
            device_id=getattr(settings, 'TEXTBEE_DEVICE_ID', '').strip(),
            timeout=getattr(settings, 'TEXTBEE_TIMEOUT', 15),
        )
    api_key = getattr(settings, 'ESMSAFRICA_API_KEY', '').strip()
    if api_key:
        return EsmsAfricaProvider(
            api_key=api_key,
            sender_id=getattr(settings, 'ESMSAFRICA_SENDER_ID', '').strip(),
            timeout=getattr(settings, 'ESMSAFRICA_TIMEOUT', 15),
        )
    if getattr(settings, 'SIMULATE_UNWIRED_CHANNELS', 'fail') == 'success':
        return SimulatedSmsProvider()
    return None


def get_whatsapp_provider():
    token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '').strip()
    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '').strip()
    if not token or not phone_number_id:
        return None
    return WhatsAppCloudProvider(
        access_token=token,
        phone_number_id=phone_number_id,
        api_version=getattr(settings, 'WHATSAPP_API_VERSION', 'v22.0').strip(),
        timeout=getattr(settings, 'WHATSAPP_TIMEOUT', 15),
    )
