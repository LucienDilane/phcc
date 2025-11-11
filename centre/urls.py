# project/urls.py (Votre fichier d'URLs principal)

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

     #Vue d'API
    path('api/v1/', include('users.api.urls')), 
    path('api/', include('medical_data.api.urls')),
    #Fin vues d'API
    path('', include('public_site.urls')),
    path('patient/', include('patients.urls')),  
]