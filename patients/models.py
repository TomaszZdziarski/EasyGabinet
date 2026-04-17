from django.db import models
from django.conf import settings
import os
from uuid import uuid4
from dentists.models import dentistProfile



#def validate_pesel(value):    # Check if the value is exactly 11 digits long and contains only digits
    #if len(value) != 11 or not re.match(r'^\d{11}$', value):
        #raise ValidationError('PESEL must be exactly 11 digits long.')

def document_upload_path(instance, filename):
    extension = os.path.splitext(filename)[1].lower()
    if extension in ['.jpeg', '.jpg', '.png']:
        return os.path.join('xrays', filename)
    else:
        return os.path.join('documents', filename)


class Document(models.Model):
    patient = models.ForeignKey('PatientProfile', related_name='documents', on_delete=models.CASCADE)
    file = models.FileField(upload_to=document_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} for {self.patient.user.username}"



class PatientProfile(models.Model):

    USER_TYPE_CHOICES = (('dentist', 'Dentysta'),('patient', 'Pacjent'),)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True,related_name='patientProfile')
    password = models.CharField(max_length=20, null=True, blank=False,default=str)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='media/', null=True, blank=True,default=str)
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)

    linked_dentist = models.ForeignKey(dentistProfile, null=True, blank=True, on_delete=models.SET_NULL)


    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

class Something(models.Model):
    owner = models.ForeignKey(PatientProfile, null=True, blank=True,on_delete=models.CASCADE)










