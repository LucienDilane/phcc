# main_views.py

from django.shortcuts import render

# Vues pour les pages statiques (templates/index.html, templates/about.html, etc.)
def home_view(request):
    """Rend la page d'accueil (index.html)."""
    return render(request, 'index.html', {})

def about_view(request):
    """Rend la page À Propos (about.html)."""
    return render(request, 'about.html', {})

def contact_view(request):
    """Rend la page Contact (contact.html)."""
    return render(request, 'contact.html', {})