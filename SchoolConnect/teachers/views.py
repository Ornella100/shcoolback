from django.db import models
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .models import Teacher
from .serializers import TeacherSerializer


class TeacherViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.user.school_id
        if not school_id:
            return Teacher.objects.none()
        queryset = Teacher.objects.filter(school_id=school_id).prefetch_related('subjects')
        search = self.request.query_params.get('search', '').strip()
        active = self.request.query_params.get('active')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search)
                | models.Q(last_name__icontains=search)
                | models.Q(phone_number__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(specialty__icontains=search)
            ).distinct()
        if active in ('true', 'false'):
            queryset = queryset.filter(is_active=(active == 'true'))
        return queryset

    def _staff_required(self, request):
        return bool(request.user.school_id and request.user.account_type == 'STAFF')

    def create(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
