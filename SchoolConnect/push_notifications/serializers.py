from rest_framework import serializers

from .models import PushSubscription


class PushSubscriptionSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=2048)
    keys = serializers.DictField()

    def validate_keys(self, value):
        p256dh, auth = value.get('p256dh'), value.get('auth')
        if not p256dh or not auth:
            raise serializers.ValidationError('Clés de notification manquantes.')
        return {'p256dh': str(p256dh), 'auth': str(auth)}

    def save(self, user):
        keys = self.validated_data['keys']
        subscription, _ = PushSubscription.objects.update_or_create(
            endpoint=self.validated_data['endpoint'],
            defaults={'user': user, 'school': user.school, 'p256dh': keys['p256dh'], 'auth': keys['auth'], 'active': True},
        )
        return subscription
