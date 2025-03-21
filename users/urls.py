from django.urls import path
from . import views

urlpatterns = [

    path('', views.profiles, name='profiles'), # name=profiles will be used in link html navbar
]