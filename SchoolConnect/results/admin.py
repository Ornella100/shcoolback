from django.contrib import admin

from .models import Assessment, StudentScore, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'school', 'coefficient', 'created_at']
    list_filter = ['school']
    search_fields = ['name', 'school__name']


class StudentScoreInline(admin.TabularInline):
    model = StudentScore
    extra = 0
    autocomplete_fields = ['student']


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'classroom', 'date', 'max_score', 'school']
    list_filter = ['school', 'annee', 'classroom', 'subject']
    search_fields = ['title', 'classroom__name', 'subject__name']
    inlines = [StudentScoreInline]


@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):
    list_display = ['student', 'assessment', 'score', 'updated_at']
    list_filter = ['assessment__school', 'assessment__annee', 'assessment__subject']
    search_fields = ['student__first_name', 'student__last_name', 'assessment__title']
