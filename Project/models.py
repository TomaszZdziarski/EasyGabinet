from django.db import models


# Create your models here.
# w admin.py mówisz z których pól może user korzystać


# PODMIANY TU MOGĄ WYMAGAĆ ZROBIENIA NOWEJ MIGRACJI !

class NewPatient(models.Model):

    username = models.CharField(max_length=64, null=True, blank=False,default=str,unique=True)
    name = models.CharField(max_length=64, null=True, blank=False,default=str)
    surname = models.CharField(max_length=64, null=True, blank=False,default=str)
    dob = models.DateTimeField(null=True, blank=True)
    pesel = models.CharField(max_length=11, null=True, blank=True,default=int)
    phone_number = models.CharField(max_length=12, null=True, blank=True,default=str)
    email = models.EmailField(null=True, blank=False,default=str)
    password = models.CharField(max_length=20, null=True, blank=True,default=str)
    photo = models.ImageField(upload_to='media/', null=True, blank=True,default=str)
    docs = models.FileField(upload_to='documents/', null=True, blank=True,default=str)

    def __str__(self):
        return self.name_and_surname()

    def name_and_surname(self):
        return '{} ({})'.format(self.name,self.surname)


