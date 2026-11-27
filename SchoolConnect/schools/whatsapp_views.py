from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SchoolWhatsAppConnection


class SchoolWhatsAppConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = request.user.school
        if not school or request.user.account_type != 'STAFF':
            return Response({'detail': 'Seul un compte du personnel scolaire peut configurer WhatsApp.'}, status=403)
        connection = SchoolWhatsAppConnection.objects.filter(school=school).first()
        return Response({
            'connected': bool(connection),
            'phone_number_id': connection.phone_number_id if connection else '',
            'has_token': bool(connection and connection.encrypted_access_token),
        })

    def put(self, request):
        school = request.user.school
        if not school or request.user.account_type != 'STAFF':
            return Response({'detail': 'Seul un compte du personnel scolaire peut configurer WhatsApp.'}, status=403)
        phone_number_id = str(request.data.get('phone_number_id', '')).strip()
        token = str(request.data.get('access_token', '')).strip()
        if not phone_number_id:
            return Response({'phone_number_id': ['Identifiant du numéro requis.']}, status=400)
        with transaction.atomic():
            connection, _ = SchoolWhatsAppConnection.objects.get_or_create(
                school=school,
                defaults={'phone_number_id': phone_number_id, 'encrypted_access_token': ''},
            )
            connection.phone_number_id = phone_number_id
            if token:
                connection.set_access_token(token)
            elif not connection.encrypted_access_token:
                return Response({'access_token': ['Jeton d’accès requis pour la première configuration.']}, status=400)
            connection.save()
        return Response({'connected': True, 'phone_number_id': connection.phone_number_id, 'has_token': True})

    def delete(self, request):
        school = request.user.school
        if not school or request.user.account_type != 'STAFF':
            return Response({'detail': 'Seul un compte du personnel scolaire peut gérer WhatsApp.'}, status=403)
        SchoolWhatsAppConnection.objects.filter(school=school).delete()
        return Response(status=204)
