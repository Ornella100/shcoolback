from django.contrib import admin

from .models import FeeInvoice, FeePayment


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ['recorded_by', 'created_at']


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'classroom', 'amount', 'due_date', 'status', 'school']
    list_filter = ['school', 'annee', 'classroom', 'status', 'due_date']
    search_fields = ['title', 'student__first_name', 'student__last_name', 'student__matricule']
    inlines = [FeePaymentInline]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'amount', 'method', 'paid_at', 'reference', 'recorded_by']
    list_filter = ['method', 'paid_at', 'invoice__school', 'invoice__annee']
    search_fields = ['invoice__student__first_name', 'invoice__student__last_name', 'reference']
    readonly_fields = ['recorded_by', 'created_at']
