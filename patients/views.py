from django.shortcuts import render, get_object_or_404,redirect
from .models import PatientProfile,Document
from dentists.models import dentistProfile
from dentists.models import Article
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .forms import PatientProfileForm
from django.contrib.auth.models import User
from patients.utils import searchArticles
from .forms import DocumentUploadForm
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from appointments.utils import update_appointments_status
from django.utils import timezone
from django.contrib import messages
from .forms import CustomPatientCreationForm
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
import os
from django.conf import settings
from django.core.exceptions import PermissionDenied



# Get the custom user model
CustomUser = get_user_model()



def patient_main(request):
    articles = Article.objects.all()
    articles, search_query = searchArticles(request) # function searchArticles in utils.py
    return render(request, 'patient_site.html', {'articles': articles,'search_query':search_query})  # Pass articles to the template


# AUTHENTICATION SECTION ###
# we are using class CustomUser, USERNAME_FIELD = 'email'

class PatientPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('patients-password_reset_done')

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        if not User.objects.filter(email=email, user_type='patient').exists():
            # if we add line below redirect is no longer silent :)
            messages.error(self.request, 'No patient account found with this email. If you are a dentist, please use the dentist login page.')
            return self.render_to_response(self.get_context_data(form=form))  # re-renders the form
        return super().form_valid(form)

def patient_register(request):
    user_form = CustomPatientCreationForm()

    if request.method == 'POST':
        user_form = CustomPatientCreationForm(request.POST, request.FILES)


        if user_form.is_valid():

            email = user_form.cleaned_data.get('email').lower()

            # Check if email already exists
            if CustomUser.objects.filter(email=email).exists():
                user_form.add_error('email', 'This email is already taken. Please choose another.')
            else:
                user = user_form.save(commit=False)
                user.email = user.email.lower()
                user.user_type = 'patient'
                user.save()

                login(request, user)
                messages.success(request, f"Patient's account was created, please fill additional credentials, welcome {user.first_name}, you are logged in!")
                profile = PatientProfile.objects.get(user=user)
                return redirect('patient-account-edit', patient_id=profile.pk)


        else:
            print("User Form Errors:", user_form.errors)
            messages.error(request, "Data didn't validate.")

    return render(request, 'patient_register.html', {
        'user_form': user_form,

    })

User = get_user_model()
def login_patient(request):

    if request.user.is_authenticated:
        if hasattr(request.user, 'patientProfile'):
            return redirect('patient-account', patient_id=request.user.patientProfile.id)
        else:
            # Log out the user
            logout(request)
            messages.info(request, "You've been logged out. Please log in with your patient account if you have one.")
            return redirect('patient-login')  # Redirect to the login page

    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request,'Email does not exist!')

        user = authenticate(request,email=email, password=password)
        # it's going to check if user matches password and either return user or None

        if user is not None:
            if user.user_type == 'patient':
                login(request,user) # it will create a session for this user in DB
                messages.success(request,f'Welcome patient {user.get_full_name()}')
                return redirect('patient-account',patient_id=request.user.patientProfile.id) # it uses related name form PatientProfile model which is:related_name='patientProfile'
            elif user.user_type == 'dentist':
            # Check if a matching patient profile exists for the dentist
                try:
                    # Change to query based on the user ID
                    patient_profile = PatientProfile.objects.get(user=user)  # Check if the user has a patient profile
                    login(request, user)  # Create a session for the dentist
                    return redirect('patient-account', patient_id=patient_profile.id)
                except PatientProfile.DoesNotExist:
                    messages.error(request, 'No patient profile exists for this dentist.')
            else:
                messages.error(request, 'You are not authorized to log in as a dentist here. Use Login/Sign up button please')
        else:
            messages.error(request,'Email or Password does not existttt!')
    return render(request, 'patient_login.html') # strona na ktora cie odesle po wylogowaniu, strona z loginem

def logout_patient(request):
    logout(request) # deletes the session
    messages.success(request,'Patient successfully logged out!')
    return redirect('profiles')

@login_required(login_url='patient-login')
def patient_profile_view(request,patient_id):
    update_appointments_status()


    profile = request.user.patientProfile #this gives us logged user, it comes from related_name = 'patientProfile' from Patient model
    patient = get_object_or_404(PatientProfile, id=patient_id)

    # Check if the patient is linked to a dentist profile
    linked_dentists = profile.linked_dentists.all()


    appointments = profile.appointments.all().order_by('-date') # you dont have to use _set.all() cos we have related_name='appointments' in Appointment model,fields: dentist and patient
    canceled_appointments = patient.appointments.filter(is_cancelled=True)

    # Use the first dentist from appointments or a default dentist
    dentist = dentistProfile.objects.filter(function='manager').first() # Adjust query as needed for your logic
    if not dentist:
        dentist = dentistProfile.objects.first()

    # Use today's date as the default
    today_date = timezone.now().date()


    # Initialize the form for document upload
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.patient = patient
            document.save()
            return redirect('patient-account', patient_id=patient.id) # Redirect to a page showing documents

    else:
        form = DocumentUploadForm()


    return render(request,'patient_account.html',{
        'profile': profile,
        'appointments':appointments,
        'patient': patient,
        'form': form,
        'dentist': dentist,
        'date': today_date.strftime('%Y-%m-%d'),
        'linked_dentists':linked_dentists,
        'canceled_appointments': canceled_appointments

    })

def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    # Make sure only the owner can delete
    if document.patient.user != request.user:
        raise PermissionDenied

    document.file.delete()  # deletes from S3/filesystem
    document.delete()       # deletes from database
    return redirect('patient-account', patient_id=request.user.patientProfile.id)

# function used to create and edit patient's profile

@login_required(login_url='patient-login')
def edit_patient_account(request,patient_id):
        profile = request.user.patientProfile  # Próbujemy uzyskać profil pacjenta
        patient = get_object_or_404(PatientProfile, id=patient_id)
        form = PatientProfileForm(instance=profile) # all data pre-filled in form
        if request.method == 'POST':
            form = PatientProfileForm(request.POST,request.FILES,instance=profile)
            if form.is_valid():
                form.save()
                return redirect('patient-account',patient_id=patient.id)
            else:
                messages.error(request, 'Please correct the errors below.')

        context = {'form':form,'patient':patient}
        return render(request,'patient_form.html',context)


# Register the font
pdfmetrics.registerFont(TTFont('TimesNewRoman', os.path.join(settings.BASE_DIR, 'fonts', 'times.ttf')))

@login_required(login_url='patient-login')
def export_treatment_history_pdf(request, patient_id):

    # Get the patient profile and appointments
    patient = get_object_or_404(PatientProfile, id=patient_id)


    appointments = patient.appointments.all().order_by('-date')
    # Debugging output
    print(f"Found {appointments.count()} appointments for {patient.user.get_full_name()}")

    # Create a response object for PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{patient.user.get_full_name()}_treatment_history.pdf"'

    # Create a PDF canvas
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Title
    p.setFont('TimesNewRoman', 16)
    p.drawString(100, height - 50, f"Treatment History for {patient.user.get_full_name()}")

    # Initialize the y position
    y = height - 100

    # Loop through appointments and add them to the PDF
    p.setFont('TimesNewRoman', 12)

    appointments_count = appointments.count()
    for appointment in appointments:

        if y < 100:  # Add a new page if space runs out
            p.showPage()
            p.setFont('TimesNewRoman', 12)
            y = height - 50


        p.drawString(60, y, f"Nr: {str(appointments_count)}")
        p.drawString(100, y, f"Appointment with {appointment.dentist.user.get_full_name()} on {appointment.date} at {appointment.start_time},status: {appointment.status}")
        y -= 20
        p.drawString(120, y, f"Diagnosis: {appointment.diagnosis}")
        y -= 20
        p.drawString(120, y, f"Treatment: {appointment.description}")
        y -= 40  # Add extra space between appointments

        appointments_count -=1
        # Finalize the PDF and return the response
    p.showPage()
    p.save()
    return response




