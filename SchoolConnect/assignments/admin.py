from django.contrib import admin

from .models import Assignment, AssignmentSubmission


class AssignmentSubmissionInline(admin.TabularInline):
    model = AssignmentSubmission
    extra = 0
    autocomplete_fields = ['student']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'classroom', 'subject', 'assigned_date', 'due_date', 'school']
    list_filter = ['school', 'annee', 'classroom', 'subject', 'due_date']
    search_fields = ['title', 'classroom__name', 'subject__name']
    inlines = [AssignmentSubmissionInline]


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'assignment', 'status', 'score', 'submitted_at', 'updated_at']
    list_filter = ['assignment__school', 'assignment__annee', 'status']
    search_fields = ['student__first_name', 'student__last_name', 'assignment__title']
