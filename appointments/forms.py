from django import forms
from .models import Appointment, AppointmentPurpose
from dentists.models import DentistSchedule
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


APPOINTMENT_DURATION = timedelta(minutes=30)  # standard duration, change here if needed


class AppointmentForm(forms.ModelForm):

    purpose = forms.ModelChoiceField(queryset=AppointmentPurpose.objects.none(), required=False, empty_label="---")

    start_time = forms.ChoiceField(
        widget=forms.Select(attrs={'id': 'id_start_time'}),
        label='Start Time'
    )

    class Meta:
        model = Appointment
        fields = ['purpose', 'custom_purpose', 'dentist', 'date', 'start_time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'id': 'id_date'}),
            'custom_purpose': forms.TextInput(attrs={
                'maxlength': '25',
                'placeholder': 'Enter custom purpose',
                'title': 'Maximum 30 characters allowed.'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.schedule = kwargs.pop('schedule', None)
        self.date = kwargs.pop('date', None)
        self.dentist = kwargs.pop('dentist', None)

        super(AppointmentForm, self).__init__(*args, **kwargs)

        if self.dentist:
            self.fields['purpose'].queryset = AppointmentPurpose.objects.filter(owner=self.dentist)

        if self.schedule and self.date and self.dentist:
            self.fields['start_time'].choices = self.generate_time_choices(self.schedule)

        for name, field in self.fields.items():
            field.widget.attrs.update({'class': 'input'})

    def clean_date(self):
        selected_date = self.cleaned_data.get('date')
        if selected_date and self.dentist:
            day_of_week = selected_date.weekday()
            if not DentistSchedule.objects.filter(dentist=self.dentist, day_of_week=day_of_week).exists():
                raise ValidationError(
                    "The selected date does not have a schedule for the chosen dentist. "
                    "Please choose an available day. If unsure, check the calendar (link top of the page)."
                )
        return selected_date

    def generate_time_choices(self, schedule):
        if not self.date or not self.dentist:
            return []

        booked_appointments = Appointment.objects.filter(
            dentist=self.dentist,
            date=self.date,
            status='booked'
        )
        booked_times = {
            datetime.combine(datetime.today(), appt.start_time).strftime('%H:%M')
            for appt in booked_appointments
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

    def clean(self):
        cleaned_data = super().clean()
        purpose = cleaned_data.get('purpose')
        custom_purpose = cleaned_data.get('custom_purpose')

        if not purpose and not custom_purpose:
            raise ValidationError("You have to fill at least one of fields 'purpose' or 'custom purpose'.")

        start_time_str = cleaned_data.get('start_time')
        if start_time_str:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            self.check_appointment_overlap(start_time)

        return cleaned_data

    def check_appointment_overlap(self, start_time):
        date = self.cleaned_data.get('date')
        dentist = self.cleaned_data.get('dentist')

        if date and dentist:
            start_datetime = timezone.make_aware(datetime.combine(date, start_time))
            end_datetime = start_datetime + APPOINTMENT_DURATION

            appointment_id = self.instance.pk if self.instance and self.instance.pk else None

            overlapping_appointments = Appointment.objects.filter(
                dentist=dentist,
                date=date,
                status='booked'
            ).exclude(pk=appointment_id)

            for appointment in overlapping_appointments:
                existing_start = timezone.make_aware(datetime.combine(appointment.date, appointment.start_time))
                existing_end = existing_start + appointment.duration
                if (start_datetime < existing_end) and (end_datetime > existing_start):
                    raise ValidationError("This appointment overlaps with an existing appointment.")


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