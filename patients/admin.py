from django.contrib import admin
from .models import PatientProfile,Something
from dentists.models import Review,Tag

# Register your models here.

admin.site.register(Review)
admin.site.register(Tag)

class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('get_first_name', 'get_last_name', 'date_of_birth', 'address', 'phone_number', 'id')  # lista wyswietlanych kolumn w panelu admin

    def get_first_name(self, obj):
        return obj.user.first_name
        get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name
        get_last_name.short_description = 'Last Name'

admin.site.register(PatientProfile, PatientProfileAdmin)
admin.site.register(Something)



