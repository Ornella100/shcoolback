from rest_framework import permissions, viewsets

from .models import ScheduleSlot
from .serializers import ScheduleSlotSerializer


class ScheduleSlotViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSlotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        school_id = self.request.user.school_id
        if not school_id:
            return ScheduleSlot.objects.none()
        qs = ScheduleSlot.objects.filter(school_id=school_id).select_related(
            'annee', 'classroom', 'subject', 'teacher',
        )
        annee_id = self.request.query_params.get('annee')
        classroom_id = self.request.query_params.get('classe')
        if annee_id:
            qs = qs.filter(annee_id=annee_id)
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id)
        return qs

    def perform_create(self, serializer):
        classroom = serializer.validated_data['classroom']
        serializer.save(
            school_id=self.request.user.school_id,
            annee=classroom.annee,
        )

    def perform_update(self, serializer):
        classroom = serializer.validated_data.get(
            'classroom', serializer.instance.classroom,
        )
        serializer.save(annee=classroom.annee)
