from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.contrib.auth import get_user_model



class CustomUserManager(BaseUserManager):


    def _create_user(self, email, password=None, **extra_fields):
        """        Creates and returns a user with an email and password.        """
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """        Creates and returns a superuser with an email and password.        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)


        return self.create_user(email, password, **extra_fields)




class CustomUser(AbstractBaseUser, PermissionsMixin):

    USER_TYPE_CHOICES = (('patient', 'Patient'),('dentist', 'Dentist'),('op', 'Op'),)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='op')
    #username = models.CharField(max_length=64, null=True, blank=False, default='op', unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    objects = CustomUserManager()
    pesel = models.CharField(max_length=11, unique=True,null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Add any additional required fields here


    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()



class dentistProfile(models.Model):

    USER_TYPE_CHOICES = (('dentist', 'Dentysta'),('patient', 'Pacjent'),)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='dentist')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='dentistProfile') # related name is used to create an instance of profile
    particip_project = models.ManyToManyField('Project', blank=True)
    phone_number = models.CharField(max_length=12, null=True, blank=True,default=str)
    password = models.CharField(max_length=20, null=True, blank=True,default=str)
    photo = models.ImageField(upload_to='media/', null=True, blank=True,default=str)
    short_intro = models.CharField(max_length=200, blank=True, null=True, default="This is a default bio. User has not added a bio yet.")
    bio = models.TextField(blank=True, null=True)
    university = models.CharField(max_length=64, null=True, blank=True,default=str)
    docs = models.FileField(upload_to='documents/', null=True, blank=True,default=str)
    function_choices = {"dentist":"Dentist","manager":"Manager","owner":"Owner"}
    function = models.CharField(choices=function_choices,null=True, blank=True,default="dentist")
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    social_website = models.CharField(max_length=2000, null=True, blank=True)

    # Alternatively, if you want to handle cases where first_name or last_name might be missing:
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    def __str__(self):
        return self.get_full_name()

class DentistSchedule(models.Model):

    dentist = models.ForeignKey(dentistProfile, on_delete=models.CASCADE,related_name='schedules')
    day_of_week = models.IntegerField(choices=[(0, 'Monday'),(1, 'Tuesday'),(2, 'Wednesday'),(3, 'Thursday'),(4, 'Friday'),(5, 'Saturday'),(6, 'Sunday'),])
    start_time = models.TimeField()
    end_time = models.TimeField()
    id = models.UUIDField(default=uuid.uuid4, unique=True,primary_key=True, editable=False)



    def __str__(self):
        return f"{self.dentist} - {self.get_day_of_week_display()}: {self.start_time} to {self.end_time}"

class Something(models.Model):
    owner = models.ForeignKey(dentistProfile, null=True, blank=True,on_delete=models.CASCADE)

class Skill(models.Model):

    owner = models.ForeignKey(dentistProfile, null=True, blank=True,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, blank=True, null=True)
    tags = models.ManyToManyField('Tag',blank=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    skill_image = models.ImageField(upload_to='media/', null=True, blank=True,default=str)

    def __str__(self):
        return str(self.name)


class Project(models.Model):

    owner = models.ForeignKey(dentistProfile, null=True, blank=True,on_delete=models.CASCADE)
    skill_used = models.ManyToManyField(Skill, blank=True)
    project_image = models.ImageField(upload_to='media/',null=True, blank=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    tags = models.ManyToManyField('Tag',blank=True)
    vote_total = models.IntegerField(default=0, null=True, blank=True)
    vote_ratio = models.IntegerField(default=0, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,primary_key=True,editable=False)

    def getVoteCount(self):
        reviews = self.review_set.all()
        upVotes = reviews.filter(value='up').count()
        vote_total = reviews.count()

        vote_ratio = (upVotes / vote_total) * 100 if vote_total > 0 else 0

        self.vote_total = vote_total
        self.vote_ratio = vote_ratio
        self.save()

    @property
    def reviewers(self):
        return self.review_set.all().values_list('owner__id', flat=True)

    def __str__(self):
        return str(self.name)

class Review(models.Model):   # MULTIPLE REVIEWS FOR 1 PROJECT

    VOTE_TYPE = (('up', 'Up Vote'), ('down', 'Down Vote'),)
    owner = models.ForeignKey(dentistProfile, on_delete=models.CASCADE, null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE) # ONE TO MANY REL
    body = models.TextField(null=True, blank=True)
    value = models.CharField(max_length=200, choices=VOTE_TYPE)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    def __str__(self):
        return self.value

class Tag(models.Model):

    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,primary_key=True, editable=False)

    def __str__(self):
        return self.name

User = get_user_model()
class Article(models.Model):

    user = models.ForeignKey(CustomUser, related_name='articles', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)  # Title of the article
    content = models.TextField()               # Main content of the article
    publication_date = models.DateTimeField(auto_now_add=True)  # Date when the article was published
    author = models.ForeignKey(dentistProfile, on_delete=models.CASCADE, related_name='articles')  # Optional: link to the author
    id = models.UUIDField(default=uuid.uuid4, unique=True,primary_key=True, editable=False)

    def __str__(self):
        return self.title  # Return the title when the object is printed

    class Meta:
        ordering = ['-publication_date']  # Order articles by publication date, newest first


