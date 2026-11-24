import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Message
from .services import send_message
from push_notifications.services import send_push

logger = logging.getLogger(__name__)


@shared_task
def send_message_task(message_id):
    with transaction.atomic():
        message = Message.objects.select_for_update().filter(
            id=message_id,
            status__in=[Message.Status.EN_ATTENTE, Message.Status.BROUILLON],
        ).first()
        if message is None:
            return
        message.status = Message.Status.EN_COURS
        message.save(update_fields=['status'])
    try:
        send_message(message)
        message.refresh_from_db(fields=['status'])
        if message.created_by_id:
            send_push(
                message.created_by,
                'Campagne terminée' if message.status != Message.Status.ECHEC else 'Échec de campagne',
                'Consultez SchoolConnect pour voir le résultat de votre envoi.',
                '/messages',
            )
    except Exception:
        message.status = Message.Status.ECHEC
        message.save(update_fields=['status'])
        if message.created_by_id:
            send_push(message.created_by, 'Échec de campagne', 'Consultez SchoolConnect pour vérifier votre envoi.', '/messages')
        raise


@shared_task
def dispatch_due_messages():
    """Met en file les campagnes arrivées à échéance et récupère les tâches perdues."""
    now = timezone.now()
    due_ids = list(
        Message.objects.filter(
            status=Message.Status.PLANIFIE,
            scheduled_at__lte=now,
        ).order_by('scheduled_at').values_list('id', flat=True)[:100]
    )
    stale_queue_ids = list(
        Message.objects.filter(
            status=Message.Status.EN_ATTENTE,
            queued_at__lte=now - timedelta(minutes=2),
        ).order_by('queued_at').values_list('id', flat=True)[:100]
    )

    queued = 0
    for message_id in due_ids:
        claimed = Message.objects.filter(
            id=message_id,
            status=Message.Status.PLANIFIE,
            scheduled_at__lte=now,
        ).update(status=Message.Status.EN_ATTENTE, queued_at=now)
        if not claimed:
            continue
        try:
            send_message_task.delay(message_id)
        except Exception:
            Message.objects.filter(
                id=message_id, status=Message.Status.EN_ATTENTE,
            ).update(status=Message.Status.PLANIFIE, queued_at=None)
            logger.exception('Impossible de mettre la campagne %s en file', message_id)
        else:
            queued += 1

    for message_id in stale_queue_ids:
        refreshed = Message.objects.filter(
            id=message_id,
            status=Message.Status.EN_ATTENTE,
            queued_at__lte=now - timedelta(minutes=2),
        ).update(queued_at=now)
        if not refreshed:
            continue
        try:
            send_message_task.delay(message_id)
        except Exception:
            logger.exception('Impossible de relancer la campagne en attente %s', message_id)
        else:
            queued += 1
    return queued
