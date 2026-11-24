from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'school', 'phone_number', 'specialty', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('first_name', 'last_name', 'phone_number', 'email')
