import json
import logging

from django.conf import settings

from .models import PushSubscription

logger = logging.getLogger(__name__)


def send_push(user, title, body, url='/'):
    """Deliver a small, non-sensitive browser notification to all user's devices."""
    if not (settings.WEB_PUSH_VAPID_PUBLIC_KEY and settings.WEB_PUSH_VAPID_PRIVATE_KEY and settings.WEB_PUSH_VAPID_CLAIMS_EMAIL):
        return 0
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.error('Push disabled: install pywebpush from backend requirements.')
        return 0

    payload = json.dumps({'title': title[:100], 'body': body[:240], 'url': url})
    sent = 0
    for subscription in PushSubscription.objects.filter(user=user, active=True).iterator():
        try:
            webpush(
                subscription_info={'endpoint': subscription.endpoint,
                    'keys': {'p256dh': subscription.p256dh, 'auth': subscription.auth}},
                data=payload,
                vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.WEB_PUSH_VAPID_CLAIMS_EMAIL}'},
                ttl=3600,
            )
            sent += 1
        except WebPushException as exc:
            response = getattr(exc, 'response', None)
            if response is not None and response.status_code in (404, 410):
                subscription.active = False
                subscription.save(update_fields=['active', 'updated_at'])
            else:
                logger.warning('Push delivery failed (subscription %s): %s', subscription.pk, exc)
    return sent
