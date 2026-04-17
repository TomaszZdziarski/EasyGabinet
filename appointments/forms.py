from django import forms
from .models import Appointment,AppointmentPurpose
from dentists.models import DentistSchedule
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta




class AppointmentForm(forms.ModelForm):


    purpose = forms.ModelChoiceField(queryset=AppointmentPurpose.objects.none(), required=False, empty_label="---")
    # two choices for duration
    DURATION_CHOICES = [('30', '30 minutes')]
    duration = forms.ChoiceField(choices=DURATION_CHOICES, label="Duration")

    start_time = forms.ChoiceField(
        widget=forms.Select(attrs={'id': 'id_start_time'}),
        label='Start Time'
    )


    class Meta:
        model = Appointment
        fields = ['duration','purpose','custom_purpose','dentist','date','start_time', ]
        widgets = { 'date': forms.DateInput(attrs={'type': 'date','id': 'id_date'}),
                    'custom_purpose': forms.TextInput(attrs={ 'maxlength': '25','placeholder': 'Enter custom purpose','title': 'Maximum 30 characters allowed.'  # Tooltip
                                                              }),
                    } # if DateTimeInput the date won't be prefilled properly

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Remove 'user' from kwargs,we limit duration for patients up to 1h, so we added:user=request.user in create_appointment
        self.schedule = kwargs.pop('schedule', None)  # Pass the schedule when initializing
        self.date = kwargs.pop('date', None)  # Ensure date is passed for checking booked slots
        self.dentist = kwargs.pop('dentist', None)  # Ensure dentist is known

        super(AppointmentForm, self).__init__(*args, **kwargs)
        if self.dentist:
            self.fields['purpose'].queryset = AppointmentPurpose.objects.filter(owner=self.dentist)


        # Initialize the start_time choices dynamically
        if self.schedule and self.date and self.dentist:
            self.fields['start_time'].choices = self.generate_time_choices(self.schedule)

        #if not self.schedule:
          #  raise forms.ValidationError("This dentist doesn't work on this day.Please choose other day")

        self.fields['duration'].label = "Duration (between 30 minutes and 1 hour)"
        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})

    # methode prevents patients to make an appointment when there is no schedule for this day
    def clean_date(self):
        selected_date = self.cleaned_data.get('date')
        # Check if the dentist has a schedule for this date
        if selected_date and self.dentist:
            day_of_week = selected_date.weekday()
            # Check if there's a schedule for the selected day for certain
            if not DentistSchedule.objects.filter(dentist=self.dentist, day_of_week=day_of_week).exists():
                raise ValidationError(f"The selected date does not have a schedule for the chosen dentist."
                                      f"Please choose an available day. If unsure, check the calendar(link top of the page)")
        return selected_date

    # Function to generate start time choices according to schedules
    def generate_time_choices(self,schedule):

        # Ensure self.date and self.dentist are correct
        if not self.date or not self.dentist:
            print("Missing date or dentist information")
            return []

        # Retrieve booked appointments for the specific dentist and date
        booked_appointments = Appointment.objects.filter(
            dentist=self.dentist,
            date=self.date,
            status='booked'
        )

        # Create a set of booked start times in string format
        booked_times = {
            datetime.combine(datetime.today(), appt.start_time).strftime('%H:%M') for appt in booked_appointments
        }


        time_choices = []
        for sched in schedule:
            current_time = datetime.combine(datetime.today(), sched.start_time)
            end_time = datetime.combine(datetime.today(), sched.end_time)
            while current_time < end_time:
                time_str = current_time.strftime('%H:%M')
                if time_str not in booked_times:
                    time_choices.append((time_str, time_str))
                current_time += timedelta(minutes=30)

        return time_choices


    # ensure that patient will schedule appointment 30min only

    def clean_duration(self):
        duration_choice = self.cleaned_data['duration']
        if duration_choice != '30':
            raise forms.ValidationError("Invalid duration selected.")
        return timedelta(minutes=30)


    # ensure that patient will give us a purpose of visit and no appointment overlapping

    def clean(self):

        cleaned_data = super().clean()
        start_time_str = cleaned_data.get('start_time')
        duration = cleaned_data.get('duration')
        purpose = cleaned_data.get("purpose")
        custom_purpose = cleaned_data.get("custom_purpose")        # Ensure at least one purpose field is filled
        if not purpose and not custom_purpose:
            raise ValidationError("You have to fill at least one of fields 'purpose' or 'custom purpose'.")

            # Check for overlapping appointments
        if start_time_str and duration:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            self.check_appointment_overlap(start_time, duration)
        return cleaned_data

    def check_appointment_overlap(self, start_time, duration):

        date = self.cleaned_data.get('date')
        dentist = self.cleaned_data.get('dentist')

        if date and dentist:

            start_datetime = timezone.make_aware(datetime.combine(date, start_time))
            end_datetime = start_datetime + duration

            # Determine if this is an update or a create operation
            appointment_id = self.instance.pk if self.instance and self.instance.pk else None


            overlapping_appointments = Appointment.objects.filter(dentist=dentist,
                                                        date=date,status='booked').exclude(pk=appointment_id)



            for appointment in overlapping_appointments:
                existing_start_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.start_time))
                existing_end_datetime = existing_start_datetime + appointment.duration
                # Check if the times overlap
                if (start_datetime < existing_end_datetime) and (end_datetime > existing_start_datetime):

                    raise ValidationError("This appointment overlaps with an existing appointment.")

            if appointment_id:
                overlapping_appointments = overlapping_appointments.exclude(pk=appointment_id)




class DentistAppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment
        fields = ['diagnosis', 'description']  # Include fields that you want the user to fill out
        widgets = {'diagnosis': forms.TextInput(attrs={'class': 'form-control'}),
                   'description': forms.Textarea(attrs={'class': 'form-control'}),}



class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status']
        widgets = {'status': forms.Select(attrs={'class': 'form-control'}),}

    def __init__(self,*args,**kwargs):
        super(AppointmentStatusForm,self).__init__(*args,**kwargs)

        # Define the statuses you want to exclude
        statuses_to_exclude = ['passed']

        # Filter the choices to exclude the specified options
        self.fields['status'].choices = [(status, label) for status, label in self.fields['status'].choices
                                         if status not in statuses_to_exclude]


class AppointmentPurposeForm(forms.ModelForm):
    class Meta:
        model = AppointmentPurpose
        fields = ['purpose', 'price_PLN']