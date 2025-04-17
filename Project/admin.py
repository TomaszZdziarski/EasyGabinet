from django.contrib import admin
from .models import NewPatient  # bez kropki = relative path nie działa,module not found
from dentists.models import Review,Tag

# Register your models here.

admin.site.register(NewPatient)
admin.site.register(Review)
admin.site.register(Tag)


