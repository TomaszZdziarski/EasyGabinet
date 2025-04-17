from django.db import models
import uuid


# Create your models here.

class dentistProfile(models.Model):

    d_project = models.ManyToManyField('Project', blank=True)
    d_skill = models.ManyToManyField('Skill', blank=True)
    name = models.CharField(max_length=64, null=True, blank=False,default=str)
    surname = models.CharField(max_length=64, null=True, blank=False,default=str)
    phone_number = models.CharField(max_length=12, null=True, blank=True,default=str)
    email = models.EmailField(null=True, blank=False,default=str)
    password = models.CharField(max_length=20, null=True, blank=True,default=str)
    photo = models.ImageField(upload_to='media/', null=True, blank=True,default=str)
    description = models.TextField(null=True, blank=True,default="This is a default bio. User has not added a bio yet.")
    bio = models.TextField(max_length=50,blank=True, null=True)
    university = models.CharField(max_length=64, null=True, blank=True,default=str)
    docs = models.FileField(upload_to='documents/', null=True, blank=True,default=str)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)

class Skill(models.Model):
    #owner = models.ForeignKey(dentistProfile,  blank=True,on_delete=models.CASCADE,default=)
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,
                          primary_key=True, editable=False)
    skill_image = models.ImageField(null=True, blank=True, default="media/default.jpg")

    def __str__(self):
        return str(self.name)


class Project(models.Model):
    owner = models.ForeignKey('dentistProfile', on_delete=models.CASCADE, null=True, blank=True)
    skill_used = models.ManyToManyField('Skill', blank=True)
    project_image = models.ImageField(null=True, blank=True, default="media/default.jpg")
    name = models.CharField(max_length=200, blank=True, null=True)
    tags = models.ManyToManyField('Tag',blank=True)
    vote_total = models.IntegerField(default=0, null=True, blank=True)
    vote_ratio = models.IntegerField(default=0, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    id = models.UUIDField(default=uuid.uuid4, unique=True,primary_key=True,editable=False)

    def __str__(self):
        return str(self.name)

class Review(models.Model):   # MULTIPLE REVIEWS FOR 1 PROJECT

    VOTE_TYPE = (('up', 'Up Vote'), ('down', 'Down Vote'),)
    owner = models.ForeignKey('dentistProfile', on_delete=models.CASCADE, null=True, blank=True)
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
