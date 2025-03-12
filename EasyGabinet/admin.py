from django.contrib import admin
from .models import NewPatient  # bez kropki = relative path nie działa,module not found

# Register your models here.

admin.site.register(NewPatient)