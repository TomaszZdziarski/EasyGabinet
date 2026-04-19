from django.shortcuts import render, redirect, get_object_or_404
from .models import dentistProfile, Skill, Project, Article, DentistSchedule
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomUserCreationForm,ProfileForm,SkillForm,ProjectForm,ReviewProject,ArticleForm,DentistScheduleForm,DentistSelectionForm
from appointments.forms import AppointmentPurposeForm
from .utils import searchProfiles, searchSkills, searchProjects
from django.contrib.auth import get_user_model
from datetime import date
from patients.models import PatientProfile
from appointments.models import Appointment,AppointmentPurpose
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
from bs4 import BeautifulSoup
from django.utils import timezone
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model





# Create your views here.
@login_required
def check_patient_pesel(request):
    dentist = request.user  # Get the logged-in dentist
    matching_patients = PatientProfile.objects.filter(pesel=dentist.pesel)
    # Query patients with matching PESEL
    return render(request, 'navbar.html', {'dentist': dentist,'matching_patients': matching_patients,    })

def profiles(request):
    projects,profiles,search_query = searchProfiles(request)  # function searchProfiles in utils.py

    context = {'profiles': profiles,'search_query':search_query,'projects': projects,}
    return render(request, 'dentists/profiles.html',context)

def profile(request, pk):

    today = timezone.now().date()
    profile = get_object_or_404(dentistProfile, id=pk)
    topSkills = profile.skill_set.exclude(description__exact="") # - In short, this returns all `Skill`
    # objects related
    # to the given `profile` **except those where the description is empty**.

    otherSkills = profile.skill_set.filter(description="") # skills without admin description, shown as OTHER
    # SKILLS in template
    dentistProjects = profile.particip_project.all()
    articles = profile.articles.all()  # not article_set
    projects = profile.project_set.all()
    current_date = date.today()
    context = {'profile': profile,
               'topSkills':topSkills,
               'otherSkills':otherSkills,
               'dentistProjects':dentistProjects,
               'current_date':current_date,
               'current_year': today.year,
               'current_month': today.month,
               'projects':projects,
               'articles': articles,
               }

    return render(request, 'dentists/profile.html',context)

def skills(request):
    skills, search_query = searchSkills(request) # function searchSkills in utils.py

    context = {'skills': skills,'search_query':search_query,}
    return render(request, 'dentists/skills.html', context)

def skill(request,pk):
    single_skill = Skill.objects.get(id=pk) # to this var. will reffer appointment.html: skill.name,skill.description
    # tags = projectObj.tags.all()
    return render(request, 'dentists/skill.html', {'single_skill': single_skill})

# PROJECTS AND REVIEWS

def projects(request):
    projects, profiles, search_query = searchProjects(request)
    context = {'projects': projects, 'search_query': search_query, 'profiles': profiles}
    return render(request, 'dentists/projects.html', context)


def project(request, pk):
    project = Project.objects.get(id=pk)
    form = ReviewProject()

    if request.method == 'POST':
        form = ReviewProject(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.project = project

            if hasattr(request.user, 'dentistProfile'):
                review.owner = request.user.dentistProfile
            elif hasattr(request.user, 'patientProfile'):
                review.owner = request.user.patientProfile
            else:
                messages.error(request, 'You need a profile to leave a review.')
                return redirect('single-project', pk=project.id)

            review.save()
            project.getVoteCount()
            return redirect('single-project', pk=project.id)

    context = {'project': project, 'form': form}
    return render(request, 'dentists/project.html', context)


# ARTICLE SECTION

def article(request,pk):
    article = Article.objects.get(id=pk)
    word_count = len(article.content.split())
    minutes_to_read = max(1, round(word_count / 200))  # average reading speed is ~200 words/min
    return render(request, 'dentists/article.html', {'article': article,'minutes_to_read': minutes_to_read,})

def articles(request):

    articles = Article.objects.all()  # Fallback to all articles
    print(f"Total articles fetched: {articles.count()}")
    return render(request, 'patient_site.html')



@login_required(login_url='login')
def create_article(request,**kwargs):
    profile = request.user
    form = ArticleForm()

    if request.method =='POST':
        form = ArticleForm(request.POST,request.FILES)
        if form.is_valid():
            article = form.save(commit=False) # just get the instance/object of Skill to be able to access to it
            # and update the owner
            article.author = request.user.dentistProfile
            article.save()
            form.save_m2m()
            messages.success(request,'Article successfully added!')
            return redirect('account')

    context = {'form': form}  # to będzie nasza zmienna do pętli w html: for skill in form...
    return render(request,'dentists/article_form.html',context)

@login_required(login_url='login')
def updateArticle(request,pk):
    profile = request.user
    article = profile.articles.get(id=pk)# we reffer to attribute: related_name='articles' from PatientArticle model
    # (profile of user who is logged in), and choose the correct skill by id
    form = ArticleForm(instance=article)

    if request.method =='POST':
        form = ArticleForm(request.POST,instance=article) # we want to modify particular skill
        if form.is_valid():
            form.save()
            messages.success(request,'Skill successfully updated!')
            return redirect('account')

    context = {'form': form}  # to będzie nasza zmienna do pętli w html: for skill in form...
    return render(request,'dentists/skill_form.html',context)

@login_required(login_url='login')
def deleteArticle(request,pk):
    profile = request.user
    article = profile.articles.get(id=pk)
    if request.method == 'POST':
        article.delete()
        messages.success(request,'Skill successfully deleted!')
        return redirect('account')
    context = {'object': article}  # we called it object cos we are using one tmplate for deleting (delete_template.html)
    # and it has variable object used
    return render(request,'dentists/delete_template.html',context)



# AUTHENTICATION SECTION ###
# we are using class CustomUser, USERNAME_FIELD = 'email'

User = get_user_model()


class DentistPasswordResetView(PasswordResetView):
    template_name = 'dentists/password_reset.html'
    email_template_name = 'dentists/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')  # your dentist done URL name

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        if not User.objects.filter(email=email, user_type='dentist').exists():
            # if we add line below redirect is no longer silent :)
            messages.error(self.request, 'No dentist account found with this email. If you are a patient, please use the patient login page.')
            return self.render_to_response(self.get_context_data(form=form))  # re-renders the form
            # silent redirect, no email sent: return HttpResponseRedirect(self.success_url)
        return super().form_valid(form)


def loginUser(request):

    page = 'login'
    if request.user.is_authenticated:
        return redirect('profiles')  # prevents from entering login page from nagigation bar: ../login/
        # when user is already authenticated
    if request.method == "POST":
        email = request.POST['email'] # will corelate with login.html fields: name="email"
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request,'Email does not exist!')

        user = authenticate(request,email=email, password=password)
        # it's going to check if user matches password and either return user or None

        if user is not None:
            if user.user_type == 'dentist':
                login(request,user) # it will create a session for this user in DB
                next_url = request.POST.get('next') or request.GET.get('next')  # check both
                if next_url:                         # ADD THIS
                    return redirect(next_url)        # ADD THIS
                return redirect('account')
            else:
                messages.error(request, 'You are not authorized to log in as a patient here. Use Patient tab to log in please')
        else:
            messages.error(request, 'Invalid email or password for dentist account!')

    return render(request, 'dentists/login_register.html') # strona na ktora cie odesle po wylogowaniu, strona z loginem

def logoutUser(request):
    logout(request) # deletes the session
    messages.success(request,'User dentist successfully logged out!')
    return redirect('profiles')

def switch_to_dentist(request, next_url):
    logout(request)
    return redirect(f"/login/?next={next_url}")


def registerUser(request):
    page = 'register'  # nazwa z ulrs,ważne pętli if w login_register.html-z tego templ.,korzysta funkcja
    # login oraz register,{% if  page == 'register' %} then show form else redirect # to login page
    form = CustomUserCreationForm()
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email').lower()
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists. Please choose a different one.')
            user = form.save(commit=False)
            user.email = user.email.lower()
            user.user_type = 'dentist' # without this line signals can work inproperly,creating profiles for opposite users(dentprof for patients etc)
            user.save()
            messages.success(request,f'User account was created,welcome {user.first_name}, you are logged in!')

            login(request,user)  # this will create a session for us!
            return redirect('edit-account')
        else:
            messages.error(request,'An error has occurred during registration!')

    context = {'page': page, 'form': form}
    return render(request, 'dentists/login_register.html',context)

@login_required(login_url='login-dentist') # if they are not logged in then they will be redirected to 'login'
def userAccount(request):

    today = timezone.now().date()
    profile = request.user.dentistProfile  #this gives us logged user
    skills = profile.skill_set.all()
    projects = profile.project_set.all()  # profile odsyła do modelu,project jest innym modelem dziedziczącym z profile
    # za pomocą pola owner = models.ForeignKey('users.Profile',...
    articles = Article.objects.filter(author=profile)

    context = {'profile': profile,'skills':skills,'projects':projects,'articles':articles,'current_year':today.year,'current_month':today.month}
    return render(request,'dentists/account.html',context) # brak request wywali błąd: python TypeError: join()
    # argument must be str, bytes, or os.PathLike object, not 'dict'

@login_required(login_url='login-dentist')
def editAccount(request):
    profile = request.user.dentistProfile
    form = ProfileForm(instance=profile)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        print(f"FILES received: {request.FILES}")  # ADD
        if form.is_valid():
            try:
                instance = form.save(commit=False)
                print(f"Photo before save: {instance.photo}")  # ADD
                instance.save()
                print(f"Photo after save: {instance.photo}")   # ADD
                print(f"Photo name: {instance.photo.name}")    # ADD
            except Exception as e:
                import traceback
                print(f"SAVE ERROR: {e}")
                print(traceback.format_exc())                  # ADD
            return redirect('account')
        else:
            print(f"Form errors: {form.errors}")

    context = {'form': form}
    return render(request, 'dentists/profile_form.html', context)

@login_required(login_url='login')
def createSkill(request,**kwargs):
    profile = request.user.dentistProfile
    form = SkillForm()

    if request.method =='POST':
        form = SkillForm(request.POST,request.FILES)
        if form.is_valid():
            skill = form.save(commit=False) # just get the instance/object of Skill to be able to access to it
            # and update the owner
            skill.owner = profile
            skill.save()
            messages.success(request,'Skill successfully created!')
            return redirect('account')

    context = {'form': form}  # to będzie nasza zmienna do pętli w html: for skill in form...
    return render(request,'dentists/skill_form.html',context)

@login_required(login_url='login')
def updateSkill(request,pk):
    profile = request.user.dentistProfile
    skill = profile.skill_set.get(id=pk)# we're choosing all skills associated with this profile
    # (profile of user who is logged in), and choose the correct skill by id
    form = SkillForm(instance=skill)

    if request.method =='POST':
        form = SkillForm(request.POST,instance=skill) # we want to modify particular skill
        if form.is_valid():
            form.save()
            messages.success(request,'Skill successfully updated!')
            return redirect('account')

    context = {'form': form}  # to będzie nasza zmienna do pętli w html: for skill in form...
    return render(request,'dentists/skill_form.html',context)


def deleteSkill(request,pk):
    profile = request.user.dentistProfile
    skill = profile.skill_set.get(id=pk)
    if request.method == 'POST':
        skill.delete()
        messages.success(request,'Skill successfully deleted!')
        return redirect('account')
    context = {'object': skill}  # we called it object cos we are using one tmplate for deleting (delete_template.html)
    # and it has variable object used
    return render(request,'dentists/delete_template.html',context)

@login_required(login_url='login')
def createProject(request):
    profile = request.user.dentistProfile
    form = ProjectForm()

    if request.method == 'POST':
        form = ProjectForm(request.POST,request.FILES)
        if form.is_valid():
            project = form.save(commit=False) # just get the instance/object of Project to be able to access the object

            project.owner = profile  # and update the owner,we want newly created project to be associated with logged profile
            project.save()
            form.save_m2m() # if the field is many-to-many rel. with other model then do this to save
            return redirect('account')  # this is name from urlpatterns

    context = {"form": form}
    return render(request, 'dentists/project_form.html', context)


@login_required(login_url='login')
def updateProject(request,pk):

    profile = request.user.dentistProfile  # we're getting 1to1 rel.
    existing_project = profile.project_set.get(id=pk)  # we want to be sure that only creator of project con modyfy/delete
    form = ProjectForm(instance=existing_project) # chcesz aby otwarty form do edycji zawieral stare dane

    if request.method == 'POST':
        form = ProjectForm(request.POST,request.FILES,instance=existing_project)

        if form.is_valid():
            form.save()
            messages.success(request,'Project successfully edited!')
            return redirect('account')  # this is name from urlpatterns

    context = {"form": form}
    return render(request, 'dentists/project_form.html', context)


@login_required(login_url='login')
def deleteProject(request,pk):
    profile = request.user.dentistProfile
    project_object = profile.project_set.get(id=pk)  # we're choosing all projects associated with this profile
    # (profile of user who is logged in), and choose the correct one by id
    if request.method == 'POST':
        project_object.delete()
        messages.success(request,'Project successfully deleted!')
        return redirect('account')
    context = {'object': project_object}
    return render(request,'dentists/delete_template.html',context)

def patient_list(request):
# Assuming only authenticated dentists can access
    if request.user.is_authenticated and hasattr(request.user, 'dentistProfile'):
        patients = PatientProfile.objects.all()
        return render(request, 'dentists/patient_list.html', {'patients': patients})
    else:
        return redirect('login-dentist')  # Ensure only authorized access

def manage_schedule(request, dentist_id):
    #dentist = dentistProfile.objects.get(id=dentist_id)
    dentist = get_object_or_404(dentistProfile, id=dentist_id)

    if request.method == 'POST':
        form = DentistScheduleForm(request.POST)
        if form.is_valid():
            # Check for duplicates before saving
            day_of_week = form.cleaned_data['day_of_week']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            # Check if this schedule already exists
            if not DentistSchedule.objects.filter(dentist=dentist, day_of_week=day_of_week, start_time=start_time, end_time=end_time).exists():
                schedule = form.save(commit=False)
                schedule.dentist = dentist
                schedule.save()
            else:
                form.add_error(None, "This schedule already exists.")

            # Redirect to the same page to show the updated schedule
            return redirect('manage-schedule', dentist_id=dentist.id)
    else:
        form = DentistScheduleForm()
    # Retrieve all schedules for the dentist to display them
    schedules = DentistSchedule.objects.filter(dentist=dentist)

    return render(request, 'dentists/manage_schedule.html', {'form': form, 'dentist': dentist,'schedules':schedules})

def  delete_schedule(request,pk):

    profile = request.user.dentistProfile
    schedule = profile.schedules.get(id=pk) # profile.schedules working cos: related_name='schedules' in DentistSchedule

    if request.method == "POST":
        schedule.delete()
        messages.success(request,'Schedule successfully deleted!')
        return redirect('manage-schedule' ,profile.id)

    context = {'object': schedule}
    return render(request,'dentists/delete_template.html',context)

def add_appointment_purposes(request,dentist_id):

    dentist = get_object_or_404(dentistProfile,id=dentist_id)
    if request.method == "POST":
        form = AppointmentPurposeForm(request.POST)
        if form.is_valid():
            appointment_purpose = form.save(commit=False)
            appointment_purpose.owner = dentist
            appointment_purpose.save()
            return redirect('add-purposes', dentist_id=dentist.id)
    else:
        form = AppointmentPurposeForm()
    return render(request, 'dentists/add_purposes.html', {'form': form,'dentist': dentist,})

def delete_appointment_purpose(request, pk):
    purpose = get_object_or_404(AppointmentPurpose,id=pk)
    dentist_id = purpose.owner.id
    if request.method == "POST":
        purpose.delete()
        return redirect('add-purposes', dentist_id=dentist_id)
    context = {'object': purpose}
    return render(request,'dentists/delete_template.html',context)


# CALENDAR PART BELOW

def get_specific_weekdays(year, month, weekday):
    """    Return all dates for a specific weekday in a given month and year.    weekday: 0 for Monday, 6 for Sunday    """

    # Start from the first day of the month
    first_day = datetime(year, month, 1)
    # Find the first occurrence of the specified weekday
    first_occurrence = first_day + timedelta(days=(weekday - first_day.weekday() + 7) % 7)

    # Generate all occurrences of the weekday in the month
    days = []
    while first_occurrence.month == month:
        days.append(first_occurrence)
        first_occurrence += timedelta(days=7)
    return days

def monthly_schedule_view(request, dentist_id):

    dentist = dentistProfile.objects.get(id=dentist_id)
    # Get schedules and calculate the specific days for the current month
    schedules = DentistSchedule.objects.filter(dentist=dentist)
    current_year = datetime.now().year
    current_month = datetime.now().month
    monthly_schedule = {}
    for schedule in schedules:
        day_dates = get_specific_weekdays(current_year, current_month, schedule.day_of_week)
        monthly_schedule[schedule] = [(day_date, schedule.start_time, schedule.end_time) for day_date in day_dates]

    return render(request, 'dentists/monthly_schedule.html', {'monthly_schedule': monthly_schedule})


def generate_calendar(request, dentist_id=None, year=None, month=None, num_months=12):

    # Load all dentists for the dropdown
    dentists = dentistProfile.objects.all()

    # Set default year and month if not provided
    current_date = timezone.now()
    year = year or current_date.year
    month = month or current_date.month

    # Initialize the form variable for context
    form = None

    # Determine the default dentist if none is provided
    if not dentist_id:
        default_dentist = dentistProfile.objects.filter(function='manager').first() or dentistProfile.objects.first()
        dentist_id = default_dentist.id if default_dentist else None
    try:
        dentist = get_object_or_404(dentistProfile, id=dentist_id)
    except Exception as e:
        print(f"Error fetching dentist: {e}")
        return redirect('access-denied')

    # Handle form submission to choose dentist
    if request.method == 'POST':
        form = DentistSelectionForm(request.POST)
        if form.is_valid():
            selected_dentist = form.cleaned_data['dentist']
            return redirect('calendar', dentist_id=selected_dentist.id)
        else:
            form = DentistSelectionForm(initial={'dentist': dentist})

    html_calendars = [] # all months until end of year
    today = timezone.now().date()  # Current date for comparison
    current_time = timezone.now().time()

    # Loop to generate each month's calendar
    for i in range(num_months):

        # Without this Calculation: You'd need to manually check and adjust month and year values, especially when moving past December.
        month_offset = (month + i - 1) % 12 + 1
        year_offset = year + (month + i - 1) // 12

        # For i = 0 (November), the calculation gives:
                # month = (11 + 0 - 1) % 12 + 1 = 11
                # year = 2025 + (11 + 0 - 1) // 12 = 2025

        # Query all appointments for the given month and year
        appointments = Appointment.objects.filter(dentist=dentist, date__year=year_offset, date__month=month_offset)

        # Query schedules for the dentist
        schedules = DentistSchedule.objects.filter(dentist=dentist)

        # Create a dictionary to track appointment status for each day
        day_status = {}

        appointments_count = defaultdict(int)
        slots_per_day = defaultdict(int)

        # Calculate number of available slots for each day

        for schedule in schedules:
            for day in range(1, calendar.monthrange(year_offset, month_offset)[1] + 1):
                day_date = datetime(year_offset, month_offset, day).date()
                if day_date.weekday() == schedule.day_of_week:
                    start_time = datetime.combine(day_date, schedule.start_time)
                    end_time = datetime.combine(day_date, schedule.end_time)
                    while start_time < end_time:
                        if day_date == today and start_time.time() < current_time:
                        # Skip slots that are already in the past for today
                            start_time += timedelta(minutes=30)
                            continue
                        slots_per_day[day_date] += 1
                        start_time += timedelta(minutes=30)  # Assuming 30-minute slots

        # Mark days as booked or available based on appointments
        for appointment in appointments:
            appointments_count[appointment.date] += 1



        # Mark days according to the schedule

        for day in range(1, calendar.monthrange(year_offset, month_offset)[1] + 1):
            day_date = datetime(year_offset, month_offset, day).date()

            if day_date < today:
                day_status[day] = 'passed'
            elif day_date == today:
                # Check if there are available slots today
                if appointments_count[day_date] < slots_per_day[day_date]:
                    day_status[day] = 'available'
                else:
                    day_status[day] = 'passed'
            else:
                if appointments_count[day_date] >= slots_per_day[day_date]:
                    day_status[day] = 'passed'
                else:
                    day_status[day] = 'available'


        # Create the HTML calendar for the given month and year
        cal = calendar.HTMLCalendar(firstweekday=0)

        html_calendar = cal.formatmonth(year_offset, month_offset)
        # Modify the HTML calendar based on appointment and schedule data

        html_calendar = mark_appointments(html_calendar, day_status,dentist.id, year_offset, month_offset)
        html_calendars.append((year_offset, month_offset, html_calendar))


    context = {'calendars': html_calendars,'year': year,'month': month,'dentist':dentist,'dentists': dentists,'form':form}
    return render(request, 'dentists/calendar.html', context)

# marks appointments with css colors depending on status
def mark_appointments(html_calendar, day_status,dentist_id, year, month):

    soup = BeautifulSoup(html_calendar, 'html.parser')
    table = soup.find('table') # creates the table
    if table:
        table['class'] = table.get('class', []) + ['calendar-container'] # table css customisation

    # Apply classes to day names and day cells
    for th in table.find_all('th'):
        th['class'] = th.get('class', []) + ['day-name']

    for td in table.find_all('td'):
        td['class'] = td.get('class', []) + ['day']
        try:
            day = int(td.text)
            status = day_status[day]
            if status == 'available':
                # create link for booking
                # Create link for booking
                day_link = f"/appointments/book/{dentist_id}/{year}-{month:02}-{day:02}/"
                formatted_date = f"{year}-{month:02}-{day:02}"
                link_tag = soup.new_tag('a', href=day_link, **{'data-date': formatted_date})
                link_tag.string = td.text
                td.clear()
                td.append(link_tag)
                td['class'] = td.get('class', []) + ['available']

            elif status == 'passed':
                td['class'] = td.get('class', []) + ['passed']
        except ValueError:            # Skip cells that are not day numbers
            continue
    return str(soup)

# Add temporarily to your views.py
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def test_s3(request):
    try:
        path = default_storage.save('media/test_from_railway.txt', ContentFile(b'hello'))
        url = default_storage.url(path)
        return HttpResponse(f"SUCCESS! Path: {path} URL: {url}")
    except Exception as e:
        return HttpResponse(f"FAILED: {str(e)}")