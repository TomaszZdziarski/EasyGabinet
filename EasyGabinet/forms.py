from django.contrib.auth.password_validation import validate_password
from django.core import validators
from django import forms
from .models import NewPatient

class Patient_Form(forms.ModelForm):
    class Meta:
        model = NewPatient
        #fields = '__all__'
        fields = ['name','surname','username','password',] # ta kolejność MEGA ważna! żeby się zgadzało z formularzem wyświetlanym
