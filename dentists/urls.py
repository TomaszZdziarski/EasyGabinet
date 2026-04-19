from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import DentistPasswordResetView


urlpatterns = [

    path('all_profiles/', views.profiles, name="profiles"), # name=profiles will be used in link html navbar
    path('single_profile/<uuid:pk>/', views.profile, name='single-profile'),

    path('skill/<str:pk>/',views.skill, name="single-skill"),

    path('projects/',views.projects, name="projects"),

    path('project/<str:pk>/',views.project, name="single-project"),
    path('register-user',views.registerUser,name="register-user"),
    path('edit-account',views.editAccount,name="edit-account"),
    path('login/', views.loginUser, name="login-dentist"),
    path('logout/', views.logoutUser, name="logout"),
    path('account/', views.userAccount, name='account'),
    path('switch-to-dentist/<path:next_url>/', views.switch_to_dentist, name='switch-to-dentist'),

    path('create-skill/',views.createSkill,name='create-skill'),
    path('update-skill/<str:pk>',views.updateSkill,name='update-skill'),
    path('delete-skill/<str:pk>',views.deleteSkill,name='delete-skill'),

    path('create-project/',views.createProject,name='create-project'),
    path('update-project/<str:pk>',views.updateProject,name='update-project'),
    path('delete-project/<str:pk>',views.deleteProject,name='delete-project'),

    path('article/<str:pk>/',views.article, name="single-article"),
    path('articles/',views.articles, name="all-articles"),
    path('create-article/', views.create_article, name="create-article"),
    path('update-article/<str:pk>',views.updateArticle,name='update-article'),
    path('delete-article/<str:pk>',views.deleteArticle,name='delete-article'),

    path('patients/', views.patient_list, name='patient-list'),
    path('manage-schedule/<uuid:dentist_id>/', views.manage_schedule, name='manage-schedule'),
    path('delete-schedule/<uuid:pk>',views.delete_schedule,name='delete-schedule'),

    path('add-purposes/<uuid:dentist_id>/', views.add_appointment_purposes, name='add-purposes'),
    path('delete-appointment-purpose/<int:pk>/', views.delete_appointment_purpose, name='delete-appointment-purpose'),


    path('monthly-schedule/<uuid:dentist_id>/', views.monthly_schedule_view, name='monthly-schedule'),
    path('calendar/<uuid:dentist_id>/', views.generate_calendar, name='calendar'),
    path('calendar/', views.generate_calendar, name='calendar_no_dentist'),  # Use the same view when dentist is not chosen and you click calendar on navbar

    path('password-reset/', DentistPasswordResetView.as_view(), name='password-reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='dentists/password_reset_done.html'), name='password_reset_done'),

    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='dentists/password_reset_confirm.html'), name='password_reset_confirm'),

    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='dentists/password_reset_complete.html'), name='password_reset_complete'),
    ]
