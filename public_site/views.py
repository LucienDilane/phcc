from django.shortcuts import render

def home_page(request):
    """Page d'accueil du site."""
    return render(request, 'public_site/home.html', {'title': 'Accueil'})

def about_page(request):
    """Page 'À Propos' (Mission, Équipe)."""
    return render(request, 'public_site/about.html', {'title': 'À Propos'})

def contact_page(request):
    """Page 'Contact' (Formulaire simple ou informations de contact)."""
   
    return render(request, 'public_site/contact.html', {'title': 'Contact'})

