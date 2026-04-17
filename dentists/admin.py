from django.contrib import admin
from .models import dentistProfile,Skill,Project,Article,DentistSchedule,Something
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm,CustomUserChangeForm



CustomUser = get_user_model()

class CustomUserAdmin(UserAdmin): # fieldset,add fieldsets are very tricky to show permissions in admin

    model = CustomUser
    # The forms to add and change user instances
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('email', 'first_name', 'last_name','pesel','user_type', 'is_active', 'is_staff','is_superuser',)

    search_fields = ('email', 'first_name', 'last_name', 'user_type','pesel')
    list_filter = ('user_type', 'is_active', 'is_staff')

    # Define the fieldsets for organizing fields in the change view
    fieldsets = ((None, {'fields': ('email', 'password')}),('Personal Info', {'fields': ('first_name', 'last_name','pesel')}),
                         ('Permissions', {'fields': ('is_active', 'is_staff','is_superuser', 'user_type',)}),
                         ('Important dates', {'fields': ('last_login',)}),    )
    # Define the add fieldsets for the add user form
    add_fieldsets = (  (None, { 'classes': ('wide',),'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'user_type','pesel')} ),)
    ordering = ['email']  # Ensure ordering is by a valid field


class DentistScheduleAdmin(admin.ModelAdmin):
    list_display = ('dentist', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('dentist', 'day_of_week')
    search_fields = ('dentist__first_name',      'dentist__last_name',  )


admin.site.register(DentistSchedule,DentistScheduleAdmin)
admin.site.register(Article)
admin.site.register(Skill)
admin.site.register(Project)
admin.site.register(dentistProfile)
admin.site.register(CustomUser,CustomUserAdmin)
admin.site.register(Something)







