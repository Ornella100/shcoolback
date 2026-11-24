from django.contrib import admin

from .models import ScheduleSlot


@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = [
        'weekday', 'start_time', 'end_time', 'classroom', 'subject',
        'teacher_name', 'room', 'school',
    ]
    list_filter = ['school', 'annee', 'weekday', 'classroom']
    search_fields = ['classroom__name', 'subject__name', 'teacher_name', 'room']
