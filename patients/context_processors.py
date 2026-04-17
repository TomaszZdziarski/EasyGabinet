# myapp/context_processors.py
from .models import PatientProfile


def patient_context(request):       # Ensure the user is authenticated and has a PatientProfile
    if request.user.is_authenticated:
        try:
            patient = request.user.patientProfile  # Assume a one-to-one relationship
            return {'patient': patient}
        except PatientProfile.DoesNotExist:
            # Handle cases where a patient profile might not exist
            return {'patient': None}
    return {'patient': None}