from django.contrib import admin

from .models import AttendanceRecord, AttendanceSession


class AttendanceRecordInline(admin.TabularInline):
    model = AttendanceRecord
    extra = 0
    autocomplete_fields = ['student']


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['date', 'classroom', 'school', 'created_by', 'updated_at']
    list_filter = ['school', 'date']
    search_fields = ['classroom__name']
    inlines = [AttendanceRecordInline]


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'status', 'session', 'marked_at']
    list_filter = ['status', 'session__school', 'session__date']
    search_fields = ['student__first_name', 'student__last_name', 'student__matricule']
