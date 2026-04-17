# appointments/management/commands/send_visit_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta, datetime
from appointments.models import Appointment
import zoneinfo

class Command(BaseCommand):
    help = 'Send 24h reminder emails to patients'

    def handle(self, *args, **kwargs):

        local_tz = zoneinfo.ZoneInfo('Europe/Warsaw')
        now = timezone.now().astimezone(local_tz)  # convert to Warsaw time

        target_date = (now + timedelta(hours=24)).date()
        time_min = (now + timedelta(hours=23, minutes=30)).time()
        time_max = (now + timedelta(hours=24, minutes=30)).time()

        self.stdout.write(f"Now (Warsaw): {now}")
        self.stdout.write(f"Looking for date: {target_date}")
        self.stdout.write(f"Time window: {time_min} - {time_max}")

        all_booked = Appointment.objects.filter(status='booked', is_cancelled=False)
        self.stdout.write(f"Booked & not cancelled: {all_booked.count()}")

        with_patient = all_booked.filter(patient__isnull=False)
        self.stdout.write(f"With patient: {with_patient.count()}")

        right_date = with_patient.filter(date=target_date)
        self.stdout.write(f"On target date ({target_date}): {right_date.count()}")

        right_time = right_date.filter(start_time__range=(time_min, time_max))
        self.stdout.write(f"In time window: {right_time.count()}")

        not_notified = right_time.filter(reminder_sent_at__isnull=True)
        self.stdout.write(f"Not yet notified: {not_notified.count()}")

        for appt in not_notified:
            if appt.patient.user.email:
                self.send_reminder(appt)
                self.stdout.write(f"Reminder sent to {appt.patient.user.email}")

        self.stdout.write(f"Done. Sent {not_notified.count()} reminders.")

    def send_reminder(self, appt):
        context = {
            'patient_name': appt.patient.user.get_full_name(),
            'date': appt.date,
            'start_time': appt.start_time,
            'dentist': appt.dentist,
            'purpose': appt.purpose or appt.custom_purpose,
            'confirm_url': f"{settings.BASE_URL}/appointments/confirm/{appt.id}/",
            'cancel_url':  f"{settings.BASE_URL}/appointments/cancel/{appt.id}/",
            'tracking_url': f"{settings.BASE_URL}/appointments/track/{appt.id}/",
        }

        subject = f"Reminder: Your dental visit tomorrow at {appt.start_time.strftime('%H:%M')}"
        text_body = render_to_string('appointments/email_reminder.txt', context)
        html_body = render_to_string('appointments/email_reminder.html', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[appt.patient.user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()

        appt.reminder_sent_at = timezone.now()
        appt.save(update_fields=['reminder_sent_at'])