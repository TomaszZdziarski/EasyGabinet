from django.db import models
from patients.models import PatientProfile
from dentists.models import dentistProfile

# Create your models here.
class Message(models.Model):


    SENDER_CHOICES = [('patient', 'Patient'), ('dentist', 'Dentist')]

    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='messages')
    dentist = models.ForeignKey(dentistProfile, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)