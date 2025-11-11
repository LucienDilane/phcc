from django.urls import path
from . import views

urlpatterns = [
    # Mappe l'URL de base de l'application (ex: /)
    path('', views.home_page, name='home'),
    path('a-propos/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
]