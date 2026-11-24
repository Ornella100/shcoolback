from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushSubscription
from .serializers import PushSubscriptionSerializer


class PushConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'enabled': bool(settings.WEB_PUSH_VAPID_PUBLIC_KEY and settings.WEB_PUSH_VAPID_PRIVATE_KEY and settings.WEB_PUSH_VAPID_CLAIMS_EMAIL),
                         'public_key': settings.WEB_PUSH_VAPID_PUBLIC_KEY})


class PushSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'subscribed': PushSubscription.objects.filter(user=request.user, active=True).exists()})

    def post(self, request):
        serializer = PushSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({'subscribed': True}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        endpoint = request.data.get('endpoint')
        if endpoint:
            PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        else:
            PushSubscription.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
