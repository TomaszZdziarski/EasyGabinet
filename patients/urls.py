from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from patients import views
from dentists.views import skills
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from .views import PatientPasswordResetView


app_name = 'patients'  # add this line at the top
urlpatterns = [
    path('messaging/', include('messaging.urls')),
    path('admin_gabinet/', admin.site.urls),
    path('',skills, name="main"),
    path('patient-register/', views.patient_register, name="patient-register"),
    path('patient-login/', views.login_patient, name="patient-login"),
    path('patient-site/', views.patient_main, name="patient-site"),
    path('patient-account/<uuid:patient_id>/', views.patient_profile_view, name="patient-account"),
    path('edit-patient-account/<uuid:patient_id>/', views.edit_patient_account, name="patient-account-edit"),
    path('patient-logout/', views.logout_patient, name="patient-logout"),
    path('', include('dentists.urls')),
    path('appointments/', include('appointments.urls')),
    path('patient/<uuid:patient_id>/export-pdf/', views.export_treatment_history_pdf, name='export_pdf'),

    path('patient-password-reset/', PatientPasswordResetView.as_view(), name='patients-password-reset'),


    path('patient-password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password_reset_done.html',
    ), name='patients-password_reset_done'),

    path('patient-password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password_reset_confirm.html',
        success_url=reverse_lazy('patients-password_reset_complete')  # <-- add this
    ), name='patients-password_reset_confirm'),

    path('patient-password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password_reset_complete.html',
    ), name='patients-password_reset_complete'),


]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
