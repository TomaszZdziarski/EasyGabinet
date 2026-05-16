from django.shortcuts import render, redirect, get_object_or_404
from dentists.models import dentistProfile,DentistSchedule
from patients.models import PatientProfile
from .forms import AppointmentForm,AppointmentStatusForm,DentistAppointmentForm
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, time
from datetime import datetime, timedelta
from django.urls import reverse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from appointments.models import Appointment,AppointmentPurpose
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from .utils import update_appointments_status,check_and_update_slots,create_monthly_schedule,mark_past_slots
import calendar
from calendar import monthrange
from unidecode import unidecode
from django.http import JsonResponse


# APPOINTMENT SECTION


@login_required
def update_appointment_status(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)    # Check if the logged-in user is the dentist associated with this appointment
    dentist_profile = request.user.dentistProfile

    if appointment.dentist != dentist_profile:
        return render(request, 'appointments/access_denied.html')
        # Handle unauthorized access

    selected_date = request.GET.get('date', None)

    if request.method == 'POST':
        form = AppointmentStatusForm(request.POST, instance=appointment)
        if form.is_valid():

            new_status = form.cleaned_data['status']

        # Check if the status is being changed to 'available'
            if form.cleaned_data['status'] == 'available':
        # Delete the appointment if it's being made available again
                appointment.delete()
        # Redirect immediately after deletion
                if selected_date:
                    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                    return redirect(reverse('available-appointments', kwargs={
                        'pk': appointment.dentist.id,
                        'year': date_obj.year,           
                        'month': date_obj.month}))
                else:
                    return redirect('available-appointments', pk=appointment.dentist.id)

            else:
                # For other status changes, just save the new status
                appointment.status = new_status
                appointment.save()
                messages.success(request, f"Appointment status updated to {new_status}.")

                if selected_date:
                    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                    return redirect(reverse('available-appointments', kwargs={
                        'pk': appointment.dentist.id,
                        'year': date_obj.year,
                        'month': date_obj.month}))
                else:
                    return redirect('available-appointments', pk=appointment.dentist.id)
    else:
        form = AppointmentStatusForm(instance=appointment)

    update_appointments_status()
    return render(request, 'appointments/update_appointment_status.html', {'form':form,'appointment': appointment})



def appointment(request,pk):

    single_appointment = get_object_or_404(Appointment, id=pk)

    # Retrieve the profiles from the appointment
    patient_profile = single_appointment.patient
    assigned_dentist = single_appointment.dentist
    # Check if the user is the patient
    if request.user == patient_profile.user:
        authorized = True
        # Check if the user is a dentist and the assigned dentist for the appointment
    elif hasattr(request.user, 'dentistProfile') and request.user.dentistProfile == assigned_dentist:
        authorized = True
    else:
        authorized = False    # Deny access if the user is not authorized
    if not authorized:
        return HttpResponseForbidden("You are not authorized to view this appointment.")



    return render(request, 'appointments/appointment.html', {'single_appointment': single_appointment,'dentist':assigned_dentist,'patient':patient_profile})

def appointments(request):

    appointments = Appointment.objects.all()  # Fallback to all articles
    return render(request, 'appointments/appointments.html',{'appointments': appointments})


# no end_time field in model - we calculate end_tima dynamically when user sets duration of visit

def calculate_end_time(appointment):
    start_datetime = timezone.make_aware(datetime.combine(appointment.date, appointment.start_time))
    return start_datetime + appointment.duration

def calculate_appointment_times(date, start_time_str):
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    appointment_start = timezone.make_aware(datetime.combine(date, start_time))
    appointment_end = appointment_start + timedelta(minutes=30)
    return appointment_start, appointment_end


# opening hours (08:00 to 20:00) validation,app in present time validation,
def validate_appointment(appointment,appointment_start, appointment_end,existing_appointment_id=None):


    # Enforce opening hours (08:00 to 20:00)
    opening_time = timezone.make_aware(datetime.combine(appointment.date, datetime.strptime('08:00', '%H:%M').time()))
    closing_time = timezone.make_aware(datetime.combine(appointment.date, datetime.strptime('20:30', '%H:%M').time()))

    # can't book appointment in history
    if appointment_start < timezone.now():
        raise ValidationError("You can't book appointment in the past!")

    elif appointment_start < opening_time or appointment_end > closing_time:
        raise ValidationError("Appointments must be within operating hours (08:00 to 20:30).")


    # Check if the appointment slot is already taken
    overlap_appointments_query = Appointment.objects.filter(
            dentist=appointment.dentist,
            date=appointment.date,
            status=['booked','available']
    ).filter(
            start_time__lt=appointment_end.time(),

    ).exclude(
            start_time__gte=appointment_start.time()
    )

    if existing_appointment_id:
        overlap_appointments_query = overlap_appointments_query.exclude(id=existing_appointment_id)

    overlap_appointments = overlap_appointments_query.exists()

    if overlap_appointments:
        raise ValidationError("This time slot is already taken.")



def validate_max_appointments(user):
    # Ensure user has a patient profile
    try:
        patient_profile = user.patientProfile
    except PatientProfile.DoesNotExist:
        raise ValidationError("No linked PatientProfile found.")

    # Count existing non-completed appointments for the user
    existing_appointments_count = Appointment.objects.filter(user=user).exclude(
        Q(status='completed')
    ).count()

    if existing_appointments_count >= 3:
        raise ValidationError("You can only book up to 3 appointments. Please contact reception for more.")


def handle_validation_error(form, error):

    if hasattr(error, 'messages'):
        for error in error.messages:
            form.add_error(None, error)
    else:
        form.add_error(None, str(error))


@login_required(login_url='patient-login')
def create_appointment(request,dentist_id=None,date=None):

    # Ensure the dentist and date are retrieved properly
    if not dentist_id or not date:
        print("Missing dentist_id or date")
        return redirect('some-error-view')

    # Fetch dentist profile
    dentist = get_object_or_404(dentistProfile, id=dentist_id)
    try:
        appointment_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        print("Invalid date format")

    # Check if the user has a patient profile
    try:
        patient_profile = request.user.patientProfile
    except PatientProfile.DoesNotExist:
        # Redirect to patient profile creation if not found
        return redirect('patient-login')


    purposes = AppointmentPurpose.objects.all()
    # form = AppointmentForm(request.POST or None)
    appointment_price = None  # Initialize appointment_price to None

    # Determine the day of the week for the schedule lookup - we want the form having only schedules hours - not all 8:00-20:00

    day_of_week = appointment_date.weekday()
    schedules = DentistSchedule.objects.filter(dentist=dentist, day_of_week=day_of_week)


    if request.method == 'POST':

        form = AppointmentForm(request.POST,user=request.user,schedule=schedules, date=appointment_date,dentist=dentist)
        converted_price = request.POST.get('converted_price')
        currency = request.POST.get('currency')


        if form.is_valid():
            try:
                validate_max_appointments(request.user)


                # Extract data from form

                start_time_str = form.cleaned_data['start_time']  # This is already a time object
                dentist = form.cleaned_data['dentist']  # Ensure you are getting the dentist from the form
                date = form.cleaned_data['date']
                purpose = form.cleaned_data['purpose']


                # Calculate appointment start and end times
                appointment_start, appointment_end = calculate_appointment_times(date, start_time_str)

                # Retrieve the purpose and its price
                if purpose:
                    appointment_price = purpose.price_PLN

                # Validate appointment

                appointment = form.save(commit=False)
                appointment.user = request.user
                appointment.status = 'booked'
                appointment.purpose = purpose
                appointment.duration = timedelta(minutes=30)

                appointment.original_price_PLN = appointment_price
                appointment.converted_price = converted_price or appointment_price
                appointment.currency = currency or "PLN"


                # Assign profiles
                appointment.patient = patient_profile
                appointment.dentist = dentist


                validate_appointment(appointment,appointment_start, appointment_end)

                appointment.save()


                # Redirect to the confirmation page
                return redirect(f"{reverse('confirmation-page')}?user_type=patient")

            except ValidationError as e:    # Capture ALL validation's errors and add it to the form
                form.add_error(None, e.message)  # Add the error message to the non-field



    else: # part for 2nd scenario - initialising form with get data
        form = initialize_form_with_get_data(request,dentist_id,date)


    # Safely handle 'date' retrieval for template context
    date_for_context = form.initial.get('date') or appointment_date


    return render(request, 'appointments/book_appointment.html', {
        'form': form,
        'purposes': purposes,
        'appointment_price':appointment_price,
        'dentist': dentist,
        'dentist_id': dentist.id,
        'date': date_for_context.strftime('%Y-%m-%d') if date_for_context else appointment_date.strftime('%Y-%m-%d'),
    })

def initialize_form_with_get_data(request,dentist_id,date):

    # Fetch dentist profile
    dentist_instance = get_object_or_404(dentistProfile, id=dentist_id) if dentist_id else None
    appointment_date = datetime.strptime(date, '%Y-%m-%d').date()

    # Use the 'date' parameter directly
    try:
        date_object = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        date_object = timezone.now().date()

    # Retrieve schedules for the specific day
    day_of_week = date_object.weekday()
    schedules = DentistSchedule.objects.filter(dentist=dentist_instance, day_of_week=day_of_week)

    initial_data = {
        'date': appointment_date,
        'dentist': dentist_instance.id,
    }


    # Check if start_time is provided in the URL
    start_time_str = request.GET.get('start_time')
    if start_time_str:
        initial_data['start_time'] = start_time_str  # Use the provided start time    elif schedules.exists():        # If no start_time is provided, use the first available slot as default        first_slot = schedules.first().time_range  # Adjust according to your model        initial_data['start_time'] = first_slot  # Add the start_time to initial data


    # Initialize form
    form = AppointmentForm(initial=initial_data, schedule=schedules, date=appointment_date, dentist=dentist_instance)
    return form


@login_required(login_url='patient-login')
def confirmation_page(request):
    user_type = request.GET.get('user_type', 'patient')  # Default to 'patient' if not provided
    return render(request, 'appointments/confirmation.html',{'is_dentist': user_type == 'dentist'})  # Adjust the template path as necessary


@login_required(login_url='patient-login')
def update_appointment_patient(request,pk):

    existing_appointment = get_object_or_404(Appointment, id=pk)  # appointments to RELATED_NAME z MODELU!  related_name='appointments'
    # Check if the user is allowed to edit this appointment
    if existing_appointment.user != request.user:
        messages.error(request, 'You do not have permission to edit this appointment.')
        return redirect('access-denied')

    # Determine the appropriate form class based on the user's role
    form_class = AppointmentForm

    if request.method == 'POST':

        selected_date_str = request.POST.get('date')
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

        # Retrieve the schedule for the specific dentist on the appointment date
        schedule = DentistSchedule.objects.filter(
            dentist=existing_appointment.dentist,
            day_of_week=selected_date.weekday()
        )

        form = form_class(request.POST,request.FILES,instance=existing_appointment,user=request.user,
                          schedule=schedule,
                          date=selected_date,
                          dentist=existing_appointment.dentist)
        if form.is_valid():
            try:
                # Save form data to the appointment instance
                appointment = form.save(commit=False)

                # Extract data from form when user

                start_time_str = form.cleaned_data['start_time']
                dentist = form.cleaned_data['dentist']
                date = form.cleaned_data['date']
                purpose = form.cleaned_data['purpose']


                appointment.duration = timedelta(minutes=30)
                # Calculate the start and end times for the appointment
                appointment_start, appointment_end = calculate_appointment_times(date, start_time_str)


                # Validate appointment times
                validate_appointment(appointment,appointment_start, appointment_end)

                # save appointment for both dentist and patient
                appointment.save()
                messages.success(request,'Appointment successfully edited!')
                return redirect('confirmation-page')  # this is name from urlpatterns

            except ValidationError as e:
                # Using the simplified error handler
                handle_validation_error(form, e)


    else:
        form = form_class(instance=existing_appointment,user=request.user, schedule=DentistSchedule.objects.filter(
            dentist=existing_appointment.dentist,
            day_of_week=existing_appointment.date.weekday()
        ), date=existing_appointment.date, dentist=existing_appointment.dentist)

    context = {"form": form,"dentist_id": existing_appointment.dentist.id}
    return render(request, 'appointments/update_appointment.html', context)

# function to pass all schedules to JSON,to fetch it later with end point javascript
def get_available_times(request):
    date_str = request.GET.get('date')
    dentist_id = request.GET.get('dentist_id')

    if date_str and dentist_id:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = timezone.localtime(timezone.now()).date()
        current_time = timezone.localtime(timezone.now()).time()

        dentist_schedule = DentistSchedule.objects.filter(dentist_id=dentist_id, day_of_week=date.weekday())

        # Calculate available times
        available_times = []
        for sched in dentist_schedule:
            current_time_slot = datetime.combine(date, sched.start_time)
            end_time = datetime.combine(date, sched.end_time)

            while current_time_slot < end_time:

                time_str = current_time_slot.strftime('%H:%M')

                # Skip past times for today
                if date == today and current_time_slot.time() < current_time:
                    current_time_slot += timedelta(minutes=30)
                    continue

                # Check if the slot is booked
                if not Appointment.objects.filter(
                        dentist_id=dentist_id,
                        date=date,
                        start_time=current_time_slot.time(),
                        status='booked').exists():
                    available_times.append(time_str)

                current_time_slot += timedelta(minutes=30)

        return JsonResponse({'times': available_times})

    return JsonResponse({'times': []})

# function adds data from 2 form fields: diagnosis and description to appointment object
@login_required(login_url='dentist-login')
def update_appointment_dentist(request, pk):

    # Check if the user has a dentist profile
    user_is_dentist = hasattr(request.user, 'dentistProfile')
    existing_appointment = get_object_or_404(Appointment, id=pk)

    # Ensure dentist is authorized to edit this appointment
    if existing_appointment.dentist != request.user.dentistProfile:
        messages.error(request, 'You do not have permission to edit this appointment.')
        return redirect('access-denied')

    form_class = DentistAppointmentForm # Form specifically for dentists


    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=existing_appointment)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, 'Appointment successfully updated!')
            return redirect('available-appointments',
                            pk=appointment.dentist.pk,
                            year=appointment.date.year,
                            month=appointment.date.month
                            )
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'There was an error with your submission.')
    else:
        form = form_class(instance=existing_appointment)

    context = {"form": form,"user_is_dentist": user_is_dentist}
    return render(request, 'appointments/update_appointment.html', context)

@login_required(login_url='patient-login')

def delete_appointment(request,pk):
    # Access the PatientProfile through a related field
    profile = get_object_or_404(PatientProfile, user=request.user)

    # Use get_object_or_404 to fetch the appointment
    appointment = get_object_or_404(Appointment, id=pk, patient=profile)

    if request.method == 'POST':
        # Mark the appointment slot as available

        appointment.status = 'available'
        appointment.is_cancelled = True  # Track that it was cancelled
        appointment.save()
        messages.success(request,'Appointment successfully cancelled! You can have max 3 appointments cancelled.')

        # Use the correct UUID of the patient in the reverse call
        patient_id = str(profile.id)  # Assuming patientProfile has the UUID
        return redirect(reverse('patient-account', kwargs={'patient_id': patient_id}))

    context = {'appointment': appointment}
    return render(request,'appointments/delete_template.html',context)


def available_appointments(request, pk, date=None, year=None, month=None):

    update_appointments_status()
    today = timezone.now().date()
    profile = get_object_or_404(dentistProfile, id=pk)

    # Set year and month to current if not provided
    if not year:
        year = today.year
    if not month:
        month = today.month

    # Calculate the previous and next month
    first_of_month = datetime(year, month, 1)
    previous_month_date = first_of_month - timedelta(days=1)
    next_month_date = first_of_month.replace(day=28) + timedelta(days=4)  # This will push it to the next month
    next_month_date = next_month_date.replace(day=1)

    # Create the monthly schedule
    num_days = monthrange(year, month)[1]
    monthly_schedule = create_monthly_schedule(profile, year, month, num_days)

    # Process each day in the monthly schedule
    for date, daily_schedule in monthly_schedule.items():

        # Query appointments for the specified dentist and date
        appointments = Appointment.objects.filter(dentist=profile, date=date)

        # Check and update slots based on existing appointments
        check_and_update_slots(daily_schedule, appointments, date)

        # Mark past slots appropriately (free day or working day
        mark_past_slots(daily_schedule, date)

    selected_date = today.strftime('%Y-%m-%d')
    update_appointments_status()
    return render(request, 'appointments/available_appointments.html',
                  {  'schedule': daily_schedule,
                           'date': date,
                           'dentist': profile,
                     'selected_date': selected_date,
                     'monthly_schedule': monthly_schedule,
                     'year': year,
                     'month': month,
                     'previous_month': previous_month_date,
                     'next_month': next_month_date,
                     'current_year': today.year,
                     'current_month': today.month,
                     }
                  )



@login_required
def export_schedule_to_pdf(request):

    selected_date_str = request.GET.get('date')
    selected_date = None

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except:
            return HttpResponse("Invalid date format. Please use YYYY-MM-DD.", status=400)

    dentist = request.user.dentistProfile
    dentist_appointments = Appointment.objects.filter(dentist=dentist, date=selected_date)
    appointments_count = dentist_appointments.count()

    full_name = dentist.user.get_full_name()
    normalized_name = unidecode(full_name)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{normalized_name}_{selected_date_str}_schedule.pdf"'

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Schedule for {full_name} on: {selected_date}", styles['Title']))
    story.append(Spacer(1, 20))

    if appointments_count > 0:
        table_data = [['Nr', 'Date', 'Time', 'Patient', 'Reason', 'Status']]

        for i, appointment in enumerate(dentist_appointments, start=1):
            patient_user = appointment.user
            if hasattr(patient_user, 'patientProfile'):
                patient_name = f"{patient_user.first_name} {patient_user.last_name}"
            else:
                patient_name = f"{dentist.user.first_name} {dentist.user.last_name}"

            purpose_display = appointment.custom_purpose if appointment.custom_purpose else appointment.purpose.purpose

            table_data.append([
                str(i),
                str(appointment.date),
                str(appointment.start_time),
                Paragraph(patient_name, styles['Normal']),
                Paragraph(str(purpose_display), styles['Normal']),
                appointment.status,
            ])

        table = Table(table_data, colWidths=[30, 70, 50, 120, 150, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        last_appointment = dentist_appointments.order_by('start_time').last()
        appointment_start = timezone.make_aware(datetime.combine(selected_date, last_appointment.start_time))
        appointment_end = appointment_start + last_appointment.duration

        story.append(Paragraph(f"Total appointments on {selected_date}: {appointments_count}", styles['Normal']))
        story.append(Paragraph(f"You will be working until {appointment_end.strftime('%H:%M')}", styles['Normal']))

    else:
        story.append(Paragraph("No appointments found for this date.", styles['Normal']))

    doc.build(story)
    return response



def access_denied_view(request):
    return render(request, 'appointments/access_denied.html')

@login_required(login_url='dentist-login')
def patient_history(request, patient_id):

    try:
        # Get the patient profile and their appointments
        profile = get_object_or_404(PatientProfile, id=patient_id)
        is_patient_profile = True

    except:        # If not found, attempt to retrieve the dentist profile
        profile = get_object_or_404(dentistProfile, id=patient_id)
        is_patient_profile = False

    # Retrieve appointments based on the profile type
    if is_patient_profile:
        appointments = Appointment.objects.filter(patient=profile).order_by('-date')

    else:        # If it's a dentist, you might want to show appointments where they are the dentist
        appointments = Appointment.objects.filter(dentist=profile).order_by('-date')

    context = {'profile': profile,'appointments': appointments,'is_patient_profile': is_patient_profile,}
    return render(request, 'appointments/patient_history.html', context)


# CRON ENGINE

# appointments/views.py

def confirm_appointment(request, pk):
    appt = get_object_or_404(Appointment, id=pk)

    if appt.is_cancelled:
        return render(request, 'appointments/already_cancelled.html')
    if appt.confirmation_status == Appointment.ConfirmationStatus.CONFIRMED:
        return render(request, 'appointments/already_confirmed.html')


    appt.confirmation_status = Appointment.ConfirmationStatus.CONFIRMED
    appt.confirmed_at = timezone.now()
    appt.save(update_fields=['confirmation_status', 'confirmed_at'])
    return redirect('/appointments/confirmed/')

def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, id=pk)

    if appt.is_cancelled:
        return render(request, 'appointments/already_cancelled.html')
    if appt.confirmation_status == Appointment.ConfirmationStatus.CONFIRMED:
        return render(request, 'appointments/already_confirmed.html')

    appt.status = 'cancelled'
    appt.is_cancelled = True
    appt.confirmation_status = Appointment.ConfirmationStatus.CANCELLED
    appt.save(update_fields=['status', 'is_cancelled', 'confirmation_status'])
    return redirect('/appointments/cancelled/')

def track_email_open(request, pk):
    appt = get_object_or_404(Appointment, id=pk)
    if not appt.email_opened_at:
        appt.email_opened_at = timezone.now()
        appt.save(update_fields=['email_opened_at'])
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
    return HttpResponse(pixel, content_type='image/gif')

def confirmed_page(request):
    return render(request, 'appointments/confirmed.html')

def cancelled_page(request):
    return render(request, 'appointments/cancelled.html')







