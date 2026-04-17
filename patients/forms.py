from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import PatientProfile,Document  # Assuming you have a Document model


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']

    def __init__(self,*args,**kwargs):
        super(DocumentUploadForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})


CustomUser = get_user_model()
class CustomPatientCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Use your custom user model
        fields = ['first_name','last_name','pesel','email','password1','password2'] # when we create a user we set
        # profile_name to users 'first_name' - check def createProfile in signals.py


    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'patient'  # Set user type to patient
        if commit:
            user.save()
        return user

    # WE WANT TO OVERRIDE THIS CUSTOMUSERCREATIONFORM METHOD TO HAVE OWN STYLE

    def __init__(self,*args,**kwargs):
        super(CustomPatientCreationForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})  # ALL FIELDS CHOOSEN IN FORM WILL HAVE ATTR. CLASS:'INPUT' THIS TIME

    def clean_pesel(self):
        pesel = self.cleaned_data.get('pesel')
        if not pesel or not pesel.isdigit() or len(pesel) != 11:
            raise forms.ValidationError("PESEL must be an 11-digit number.")
        return pesel

class PatientProfileForm(forms.ModelForm):

    phone_number = forms.CharField(required=True)
    address = forms.CharField(required=True)
    date_of_birth = forms.DateField(input_formats=['%d-%m-%Y','%Y-%m-%d', '%d/%m/%Y','%d.%m.%Y'], required=True,
                                    widget=forms.DateInput(attrs={'type': 'date'})  # Use HTML5 date input
                                    )

    

    class Meta:
        model = PatientProfile
        fields = ['phone_number', 'address','date_of_birth','photo' ]


    # overriding methode to ensure that dob not in the future
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > timezone.now().date():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob

    def __init__(self,*args,**kwargs):
        super(PatientProfileForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})




