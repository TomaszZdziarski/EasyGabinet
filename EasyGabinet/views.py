from django.shortcuts import render, get_object_or_404,redirect
from .models import NewPatient
from .forms import Patient_Form
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required


def patient_main(request):

    all_info = NewPatient.objects.all()
    return(render(request,'patient_main.html',{'patient_main':all_info}))

def patient_register(request):
    form = Patient_Form()
    context = {'form': form,}
    return render(request,'register_patient.html',{'form':form})
