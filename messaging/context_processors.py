from .models import Message
from dentists.models import dentistProfile
from patients.models import PatientProfile

"""
why do i need context processors?
The problem — Django views pass data only to their own template. So if you calculate unread_count 
in your inbox_dentist view, that variable exists only in inbox.html. 
Your main.html (the navbar) knows nothing about it.

What a context processor does — it's a function that runs on every single request, regardless of which view is being 
called, and adds variables to the template context globally. Think of it like middleware but for template variables.

The flow looks like this:
User visits any page
        ↓
Django runs the view (e.g. appointments view)
        ↓
Django also runs ALL context processors
        ↓
Both results get merged into one context dict
        ↓
Template renders with everything available


A rule of thumb — if you need a variable available site-wide (logged-in user info, cart count, 
notification badges, unread messages), a context processor is the right tool. 
Django actually uses this pattern itself — {{ request.user }} works everywhere because of a 
built-in context processor called django.contrib.auth.context_processors.auth. So change in settings needed:

 # add this to:
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': 
            'messaging.context_processors.unread_messages', 

"""

def unread_messages(request):
    if not request.user.is_authenticated:
        return {'unread_count': 0}

    # Dentist
    try:
        dentist = dentistProfile.objects.get(user=request.user)
        count = Message.objects.filter(
            dentist=dentist,
            sender='patient',
            is_read=False
        ).count()

        return {'unread_count': count}
    except dentistProfile.DoesNotExist:
        pass

    # Patient
    try:
        patient = PatientProfile.objects.get(user=request.user)
        count = Message.objects.filter(
            patient=patient,
            sender='dentist',
            is_read=False
        ).count()

        return {'unread_count': count}
    except PatientProfile.DoesNotExist:
        pass

    return {'unread_count': 0}