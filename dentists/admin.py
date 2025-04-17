from django.contrib import admin
from .models import dentistProfile,Skill,Project

# Register your models here.

admin.site.register(dentistProfile)
admin.site.register(Skill)
admin.site.register(Project)
