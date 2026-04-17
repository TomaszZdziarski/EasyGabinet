from django.utils import timezone
from datetime import datetime,timedelta
from .models import Appointment
from dentists.models import DentistSchedule

def update_appointments_status():
    now = timezone.now()       # Query to find appointments that need status updates
    appointments_to_update = Appointment.objects.filter(status__in=['booked', 'available'])
    for appointment in appointments_to_update:
        appointment_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.start_time))
        if appointment_datetime < now:
            if appointment.status == 'booked':
                appointment.status = 'completed'
            elif appointment.status == 'available':
                appointment.status = 'passed'
            appointment.save()

def create_monthly_schedule(profile, year, month, num_days):
    monthly_schedule = {}
    for day in range(1, num_days + 1):
        date = datetime(year, month, day).date()
        weekday = date.weekday()
        dentist_schedules = DentistSchedule.objects.filter(dentist=profile, day_of_week=weekday)
        slots = []
        for schedule in dentist_schedules:
            current_time = datetime.combine(date, schedule.start_time)
            closing_time = datetime.combine(date, schedule.end_time)
            while current_time.time() < closing_time.time():

                end_time = current_time + timedelta(minutes=30)
                slots.append((current_time.time(), end_time.time()))
                current_time = end_time

        daily_schedule = {f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}": {'status': 'available',
                                                            'appointment_id': f"slot-{start.strftime('%H%M')}"}
                                  for start, end in slots}

        monthly_schedule[date] = daily_schedule

    return monthly_schedule

def check_and_update_slots(daily_schedule, appointments, date):

    for appointment in appointments:

        appointment_start = datetime.combine(date, appointment.start_time)
        appointment_end = appointment_start + appointment.duration

        for slot_range in daily_schedule.keys():

            # Split the time range string into start and end times
            start_str, end_str = slot_range.split(' - ')
            slot_start = datetime.combine(date, datetime.strptime(start_str, '%H:%M').time())
            slot_end = datetime.combine(date, datetime.strptime(end_str, '%H:%M').time())

            if (appointment_start < slot_end) and (appointment_end > slot_start):
                slot_range = f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                appointment_info = {'status': appointment.status, 'appointment_id': appointment.id}

                if hasattr(appointment, 'patient'):
                    appointment_info['patient'] = appointment.patient
                    if hasattr(appointment, 'dentist'):
                        appointment_info['dentist'] = appointment.dentist

                daily_schedule[slot_range] = appointment_info

def mark_past_slots(daily_schedule, date):
    for time_range, details in daily_schedule.items():
        if details['status'] == 'available':
            start_time_str = time_range.split(' - ')[0]
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            full_datetime = timezone.make_aware(datetime.combine(date, start_time))
            if full_datetime < timezone.now():
                details['status'] = 'passed'