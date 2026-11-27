"""
URL configuration for SchoolConnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import (
    csrf_view,
    login_view,
    logout_view,
    me_view,
    password_reset_confirm_view,
    password_reset_request_view,
    register_view,
)
from academics.views import (
    AnneeScolaireViewSet,
    ClasseViewSet,
    CustomFieldDefinitionViewSet,
    EleveViewSet,
)
from attendance.views import AttendanceView
from results.views import (
    AssessmentGradesView,
    AssessmentViewSet,
    BulletinView,
    SubjectViewSet,
)
from timetable.views import ScheduleSlotViewSet
from discipline.views import IncidentViewSet
from assignments.views import AssignmentSubmissionsView, AssignmentViewSet
from data_import.views import (
    ImportCommitView,
    ImportPreviewAsyncView,
    ImportPreviewStatusView,
    ImportPreviewView,
    import_columns_view,
    import_template_view,
)
from messaging.views import MessageTemplateViewSet, MessageViewSet, billing_summary_view
from parents.views import ParentViewSet, StudentGuardianViewSet
from parents.portal_views import parent_portal_summary
from reports.views import SchoolReportExportView, SchoolReportView
from fees.views import FeeBatchView, FeeInvoiceViewSet, FeePaymentsView
from push_notifications.views import PushConfigView, PushSubscriptionView
from teachers.views import TeacherViewSet
from schools.views import SchoolViewSet
from schools.whatsapp_views import SchoolWhatsAppConnectionView

router = DefaultRouter()
router.register('schools', SchoolViewSet, basename='school')
router.register('annees', AnneeScolaireViewSet, basename='annee')
router.register('classes', ClasseViewSet, basename='classe')
router.register('eleves', EleveViewSet, basename='eleve')
router.register('subjects', SubjectViewSet, basename='subject')
router.register('assessments', AssessmentViewSet, basename='assessment')
router.register('timetable', ScheduleSlotViewSet, basename='timetable')
router.register('incidents', IncidentViewSet, basename='incident')
router.register('assignments', AssignmentViewSet, basename='assignment')
router.register('fees', FeeInvoiceViewSet, basename='fee')
router.register('teachers', TeacherViewSet, basename='teacher')
router.register('custom-fields', CustomFieldDefinitionViewSet, basename='custom-field')
router.register('parents', ParentViewSet, basename='parent')
router.register('student-guardians', StudentGuardianViewSet, basename='student-guardian')
router.register('message-templates', MessageTemplateViewSet, basename='message-template')
router.register('messages', MessageViewSet, basename='message')

# Le nom "SchoolConnect" (avec le "Connect" en doré) est codé dans templates/admin/base_site.html
# plutôt qu'ici, pour éviter de manipuler du HTML via mark_safe côté Python.
admin.site.site_title = 'SchoolConnect Admin'
admin.site.index_title = 'Tableau de bord administrateur'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/csrf/', csrf_view),
    path('api/school/whatsapp/', SchoolWhatsAppConnectionView.as_view()),
    path('api/push/config/', PushConfigView.as_view()),
    path('api/push/subscription/', PushSubscriptionView.as_view()),
    path('api/register/', register_view),
    path('api/login/', login_view),
    path('api/logout/', logout_view),
    path('api/me/', me_view),
    path('api/password-reset/', password_reset_request_view),
    path('api/password-reset/confirm/', password_reset_confirm_view),
    path('api/', include(router.urls)),
    path('api/attendance/', AttendanceView.as_view()),
    path('api/assessments/<int:assessment_id>/grades/', AssessmentGradesView.as_view()),
    path('api/bulletins/', BulletinView.as_view()),
    path('api/assignments/<int:assignment_id>/submissions/', AssignmentSubmissionsView.as_view()),
    path('api/billing/summary/', billing_summary_view),
    path('api/parent-portal/summary/', parent_portal_summary),
    path('api/reports/school/', SchoolReportView.as_view()),
    path('api/reports/school/export/', SchoolReportExportView.as_view()),
    path('api/fees/generate-class/', FeeBatchView.as_view()),
    path('api/fees/<int:invoice_id>/payments/', FeePaymentsView.as_view()),
    path('api/imports/columns/', import_columns_view),
    path('api/imports/template/', import_template_view),
    path('api/imports/preview/', ImportPreviewView.as_view()),
    path('api/imports/preview-async/', ImportPreviewAsyncView.as_view()),
    path('api/imports/preview-status/<str:task_id>/', ImportPreviewStatusView.as_view()),
    path('api/imports/commit/', ImportCommitView.as_view()),
]
