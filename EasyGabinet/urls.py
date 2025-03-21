"""
URL configuration for EasyGabinet project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from EasyGabinet import views

from EasyGabinet.models import NewPatient
from .views import patient_main, patient_register, login_user

urlpatterns = [
    path('admin_gabinet/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', patient_main,name='main'),
    path('login/', views.login_user, name="login"),
    #path('logout/', views.patient_main, name="logout"),
    path('register-patient/', views.patient_register, name="register"),
    # path('registered-patient/', patient_register, name="registered"),

]
