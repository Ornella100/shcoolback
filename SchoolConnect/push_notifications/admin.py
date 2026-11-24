from django.contrib import admin

from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'active', 'updated_at')
    list_filter = ('active', 'school')
    search_fields = ('user__username', 'user__email', 'endpoint')
    readonly_fields = ('created_at', 'updated_at')
