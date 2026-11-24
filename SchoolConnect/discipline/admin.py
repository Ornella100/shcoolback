from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'student', 'classroom', 'category', 'severity',
        'status', 'reported_by', 'school',
    ]
    list_filter = ['school', 'annee', 'category', 'severity', 'status', 'date']
    search_fields = ['student__first_name', 'student__last_name', 'description', 'classroom__name']
    readonly_fields = ['reported_by', 'resolved_at', 'created_at', 'updated_at']
