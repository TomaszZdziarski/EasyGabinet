from django.shortcuts import render, get_object_or_404,redirect
from .models import NewPatient
from .forms import Patient_Form
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User

def registered(request):
    return render(request, 'patient_registered.html')

def patient_main(request):

    all_info = NewPatient.objects.all()
    return(render(request,'index.html',{'patient_main':all_info}))

def login_user(request):
    return render(request,template_name='login.html')

def logout_user(request):
    pass


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

        return redirect(patient_main)  # this is name from urlpatterns OR NOT ;) w tutorialach było name
                                           # a pycharm podkreśla jako błąd i każe robić nazwę funkcji z views.py lub jest to context z tej funkcji

    return render(request, 'register_patient.html', {'form': Patient_Form}) # 'form' kontekstucje z formularzem z forms
