from rest_framework import permissions, viewsets

from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.user.school_id
        if not school_id:
            return Incident.objects.none()
        qs = Incident.objects.filter(school_id=school_id).select_related(
            'annee', 'classroom', 'student', 'reported_by',
        )
        year_id = self.request.query_params.get('annee')
        classroom_id = self.request.query_params.get('classe')
        status_value = self.request.query_params.get('status')
        if year_id:
            qs = qs.filter(annee_id=year_id) if year_id.isdigit() else qs.none()
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id) if classroom_id.isdigit() else qs.none()
        if status_value:
            qs = qs.filter(status=status_value) if status_value in Incident.Status.values else qs.none()
        return qs
