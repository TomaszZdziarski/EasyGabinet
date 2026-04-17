from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import dentistProfile,Skill,Project,Article,DentistSchedule,Review
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from datetime import datetime, timedelta


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name','last_name','pesel','email','password1','password2'] # when we create a user we set
        # profile_name to users 'first_name' - check def createProfile in signals.py

    # WE WANT TO OVERRIDE THIS CUSTOMUSERCREATIONFORM METHOD TO HAVE OWN STYLE

    def __init__(self,*args,**kwargs):
        super(CustomUserCreationForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})  # ALL FIELDS CHOOSEN IN FORM WILL HAVE ATTR. CLASS:'INPUT' THIS TIME

    def clean_pesel(self):
        pesel = self.cleaned_data.get('pesel')

        # Check if pesel is provided
        if not pesel:
            raise forms.ValidationError("PESEL is required.")

        # Add your custom validation logic here
        if not pesel.isdigit() or len(pesel) != 11:
            raise forms.ValidationError("PESEL must be an 11-digit number.")
        return pesel

# Custom form for updating users
class CustomUserChangeForm(ModelForm):
    password = ReadOnlyPasswordHashField()
    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'first_name', 'last_name', 'is_active', 'is_staff', 'user_type','is_superuser','pesel')
        def clean_password(self):
            return self.initial["password"]

class ProfileForm(ModelForm):
    class Meta:
        model = dentistProfile
        fields = ['phone_number','photo','university','bio','particip_project','short_intro','social_website']

    def __init__(self,*args,**kwargs):
        super(ProfileForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})


class SkillForm(ModelForm):
    class Meta:
        model = Skill
        fields = '__all__'
        # we want to hide a 'owner' field from Skill model cos evertime a profile creates skill would be the owner
        # and the next profile adding same skill would set up the ownership of this skill to themselves
        exclude = ['owner']

    def __init__(self,*args,**kwargs):
        super(SkillForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        exclude = ['owner']

    def __init__(self,*args,**kwargs):
        super(ProjectForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})

class ReviewProject(ModelForm):
    class Meta:
        model = Review
        fields = ['body','value']

class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = '__all__'
        exclude = []

    def __init__(self,*args,**kwargs):
        super(ArticleForm,self).__init__(*args,**kwargs)

        for name,field in self.fields.items():
            field.widget.attrs.update({'class':'input'})


class DentistScheduleForm(ModelForm):
    class Meta:
        model = DentistSchedule
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {'day_of_week': forms.Select(),'start_time': forms.Select(),'end_time': forms.Select(),        }

    def __init__(self, *args, **kwargs):
        super(DentistScheduleForm, self).__init__(*args, **kwargs)

        # Define choices for time selection
        time_choices = self.generate_time_choices()
        # Assign the choices to the time fields
        self.fields['start_time'].widget.choices = time_choices
        self.fields['end_time'].widget.choices = time_choices

    def generate_time_choices(self):
        start_hour = 8  # start from midnight
        end_hour = 20  # till the end of the day
        interval = 30  # 30 minutes
        time_choices = []
        current_time = datetime.strptime(f'{start_hour}:00', '%H:%M')
        end_time = datetime.strptime(f'{end_hour}:59', '%H:%M')
        while current_time <= end_time:
            time_str = current_time.strftime('%H:%M')
            time_choices.append((time_str, time_str))
            current_time += timedelta(minutes=interval)
        return time_choices


# Form for selecting a dentist
class DentistSelectionForm(forms.Form):

    dentist = forms.ModelChoiceField(queryset=dentistProfile.objects.all(), label="Select Dentist")