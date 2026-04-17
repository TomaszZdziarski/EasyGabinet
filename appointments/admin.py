from django.contrib import admin
from .models import Appointment, AppointmentPurpose


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('name','dentist','patient','date','id','start_time','duration','custom_purpose','status')
    list_filter = ('date', 'status')
    #search_fields = ('purpose__name')
    #list_editable = (('status',))

@admin.register(AppointmentPurpose)
class AppointmentPurposeAdmin(admin.ModelAdmin):
    list_display = ('purpose','price_PLN')
    search_fields = ('purpose',)
