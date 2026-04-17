from django.urls import path
from appointments import views
from patients.views import export_treatment_history_pdf


urlpatterns = [
               path('appointment/<uuid:pk>/',views.appointment, name="single-appointment"),
               path('',views.appointments, name="all-appointments"),
               path('book/<uuid:dentist_id>/<str:date>/', views.create_appointment, name='create-appointment'),
               path('update-patient/<uuid:pk>/', views.update_appointment_patient, name='update-appointment-patient'),
               path('update-dentist/<uuid:pk>/', views.update_appointment_dentist, name='update-appointment-dentist'),
               path('confirmation/', views.confirmation_page, name='confirmation-page'),
               path('delete/<uuid:pk>/', views.delete_appointment, name='delete-appointment'),
               path('available/<uuid:pk>/<int:year>/<int:month>/',views.available_appointments,name='available-appointments'),
               path('update-appointment/<uuid:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
               path('export_schedule/', views.export_schedule_to_pdf, name='export_schedule'),
               path('access_denied/', views.access_denied_view, name='access-denied'),
               path('patient/<uuid:patient_id>/history/', views.patient_history, name='patient-history'),
               path('get-available-times/', views.get_available_times, name='get_available_times'),

                path('confirm/<uuid:pk>/', views.confirm_appointment, name='confirm-appointment'),
                path('cancel/<uuid:pk>/', views.cancel_appointment, name='cancel-appointment'),
                path('track/<uuid:pk>/', views.track_email_open, name='track-email-open'),
                path('confirmed/', views.confirmed_page, name='confirmed-page'),
                path('cancelled/', views.cancelled_page, name='cancelled-page'),







]