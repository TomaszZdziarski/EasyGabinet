from django.shortcuts import render, get_object_or_404,redirect
from .models import NewPatient
from dentists.models import dentistProfile,Skill,Project
from .forms import Patient_Form
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from dentists.views import skills



def patient_register(request):
    form = Patient_Form()

    if request.method == 'POST':  # saving form to database
        form = Patient_Form(request.POST,request.FILES)
        if form.is_valid():
            if User.objects.filter(username=form.cleaned_data['username']).exists(): # to podpowiedziało AI ;)
                messages.success(request, 'This username is already taken!')
            else:
                form.save()
                messages.success(request, 'Your account has been created!')

        return redirect(skills)  # this is name from urlpatterns OR NOT ;) w tutorialach było name
                                           # a pycharm podkreśla jako błąd i każe robić nazwę funkcji z views.py lub jest to context z tej funkcji

    return render(request, 'register_patient.html', {'form': Patient_Form}) # 'form' kontekstucje z formularzem z forms

def login_user(request):
    login = Project.objects.all()
    context = {'login':login}
    return render(request, 'login.html', {'form': Patient_Form})

