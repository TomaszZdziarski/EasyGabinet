from django.db import models
from uuid import uuid4
from django.contrib.auth import get_user_model
from patients.models import PatientProfile
from dentists.models import dentistProfile
from datetime import datetime, timedelta
from django.utils import timezone
import uuid


User = get_user_model()

class AppointmentPurpose(models.Model):

    owner = models.ForeignKey(dentistProfile,related_name='purposes',on_delete=models.CASCADE,null=True)
    purpose = models.CharField(max_length=100,default="Consultation")
    price_PLN = models.DecimalField(max_digits=10, decimal_places=2,default=150.00)  # Store price in PLN


    def __str__(self):
        return f"{self.purpose} - {self.price_PLN} PLN "



class Appointment(models.Model):

    start_time = models.TimeField()
    name = models.CharField(max_length=100,default='appointment')
    STATUS_CHOICES = [
                      ('available', 'Available'),
                      ('booked', 'Booked'),
                      ('passed', 'Passed'),
                      ('completed', 'Completed'),
                      ('did_not_occur', "Didn't show up, no notification"),
                      ('cancelled', 'Cancelled')
                ]
    #CURRENCY_CHOICES = [('PLN','Polski złoty'),('USD','American Dollars'),('EUR','Euro'),('UAH','Hrywna'),('JMD','Jamaican Dollars')]

    user = models.ForeignKey(User, related_name='appointments',on_delete=models.CASCADE,null=True)
    dentist = models.ForeignKey(dentistProfile, on_delete=models.CASCADE,related_name='dentist_site_appointments') # Allows you to access all appointments for a specific dentist using dentist_profile.dentist_site_appointments.all()
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, null=True, blank=True,related_name='appointments')
    date = models.DateField(default=timezone.now)
    duration = models.DurationField(default=timedelta(minutes=30))  # Duration field with a default of 30 minutes
    custom_purpose = models.CharField(max_length=25, blank=True)
    purpose = models.ForeignKey(AppointmentPurpose, on_delete=models.CASCADE,null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    id = models.UUIDField(default=uuid4, unique=True, primary_key=True, editable=False)

    diagnosis = models.CharField(max_length=25, blank=False, null=False,default="No diagnosis yet!")
    description = models.CharField(max_length=125, blank=False, null=False,default="No description yet!")

    converted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,default=0.00)
    currency = models.CharField(max_length=3, null=True, blank=True,default='PLN')

    # Add a boolean or separate model for cancellation tracking
    is_cancelled = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)



    def book(self):

        if self.status == 'available':
            self.status = 'booked' # Change status when booked

        else:
            raise ValueError("This appointment is already booked.")

    def __str__(self):
        return f"{self.name} - {self.date} {self.start_time} ({self.status})"

    def is_available(self):
        return self.status == 'available'

# CRON CONFIRMATION EMAIL

    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    class ConfirmationStatus(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'

    confirmation_status = models.CharField(
        max_length=20,
        choices=ConfirmationStatus.choices,
        default=ConfirmationStatus.PENDING,
    )
    email_opened_at = models.DateTimeField(null=True, blank=True)



