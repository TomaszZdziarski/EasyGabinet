from django.urls import path
from . import views


urlpatterns = [

    path('all_profiles/', views.profiles, name='profiles'), # name=profiles will be used in link html navbar
    path('single_profile/<str:profile_id>/', views.profile, name='single-profile'),

    path('skill/<str:skill_id>/',views.skill, name="single-skill"),

    path('projects/',views.projects, name="all-projects"),

    path('project/<str:project_id>/',views.project, name="single-project"),


]