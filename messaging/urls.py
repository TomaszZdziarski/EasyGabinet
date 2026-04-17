from django.urls import path
from . import views

urlpatterns = [
    path('inbox-dentist/', views.inbox_dentist, name='inbox'),
    path('new-message/', views.new_message, name='send-message'),
    path('conversation/<uuid:patient_id>/', views.conversation, name='conversation'),
    path('delete-message/<int:pk>/', views.delete_message, name='message-delete'),
    path('patient-inbox/', views.patient_inbox, name='patient-inbox'),
]