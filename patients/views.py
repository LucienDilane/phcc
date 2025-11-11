from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime
import json
from decimal import Decimal

from medical_data.models import Suivi, RendezVous, ReleveVital
from users.models import DetailsPatient
PatientModel=get_user_model()

# VUE DE CONNEXION (Gère la page patient_login.html)
def patient_login_view(request):
    if request.user.is_authenticated:
        return redirect('patient_dashboard')  # Redirige si déjà connecté
        
    if request.method == 'POST':
        # Ceci est un exemple simpliste. En production, utilisez des formulaires Django sécurisés.
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('patient_dashboard')
        else:
            # Gérer l'échec de la connexion
            # Vous pouvez ajouter un message d'erreur au contexte
            return render(request, 'patients/patient_login.html', {'error_message': 'Identifiants invalides.'})
            
    return render(request, 'patients/patient_login.html')

# VUE DU TABLEAU DE BORD (Accès uniquement aux utilisateurs connectés)
@login_required
def patient_dashboard_view(request):
    
    current_time = timezone.now()
    current_patient = request.user
    
    # 1. Récupération des 5 derniers Suivis/Observations (ordonnés par date décroissante)
    derniers_suivis = Suivi.objects.filter(
        patient=current_patient
    ).all()[:5]

    # NOUVEAU : On prend le plus récent pour l'indicateur clé
    dernier_suivi = derniers_suivis.first()
    suivis_additionnels = derniers_suivis[1:] if derniers_suivis.count() > 1 else None 
    
    # 2. Récupération du prochain Rendez-vous
    prochain_rdv = RendezVous.objects.filter(
        patient=current_patient,
        date_heure__gte=current_time,
        statut__in=['P', 'C']
    ).order_by('date_heure').first()

    # 3. Récupération des données de télésurveillance (Glycémie/Tension)
    # ... (le code de récupération et préparation des données de graphiques reste inchangé)
    # (Nous assumons que les variables 'dernier_releve', 'dates', etc. sont préparées ici)
    dernier_releve = None
    dates = []
    tension_systolique_data = []
    tension_diastolique_data = []
    glycemie_data = []

    if ReleveVital:
        releves_vitaux = ReleveVital.objects.filter(
            patient=current_patient
        ).order_by('-date_releve')[:15]
        
        if releves_vitaux.exists(): 
            releves_vitaux_ordonnes = list(reversed(releves_vitaux)) 

            for r in releves_vitaux_ordonnes:
                dates.append(r.date_releve.strftime("%d/%m %Hh"))
                
                # Conversion des valeurs DecimalField en float ou s'assurer que None est utilisé
                
                # Tension (souvent IntegerField, mais on assure la conversion)
                tension_systolique_data.append(r.tension_systolique)
                tension_diastolique_data.append(r.tension_diastolique)
                
                # GLYCÉMIE : Conversion nécessaire si r.glycemie est un objet Decimal
                if r.glycemie is not None:
                    # Convertit l'objet Decimal en float standard
                    glycemie_data.append(float(r.glycemie))
                else:
                    # Ajoute None pour que Chart.js ignore ce point de données
                    glycemie_data.append(None) 

    # SÉRIALISATION JSON : Utilisation de json.dumps() pour générer des chaînes JSON valides.
    # Puisque nous avons converti les Decimals en floats ci-dessus, cette étape fonctionne.
    chart_data_labels_json = json.dumps(dates)
    chart_data_tension_s_json = json.dumps(tension_systolique_data)
    chart_data_tension_d_json = json.dumps(tension_diastolique_data)
    chart_data_glycemie_json = json.dumps(glycemie_data)


    context = {
        'patient_name': current_patient.get_full_name() or current_patient.username,
        'prochain_rdv': prochain_rdv,
        'derniers_suivis': derniers_suivis,
        'suivis additionels':suivis_additionnels,
        'active_page': 'overview',
        
        'dernier_releve': releves_vitaux.first() if ReleveVital and releves_vitaux.exists() else None,
        
        'chart_data_labels_json': chart_data_labels_json,
        'chart_data_tension_s_json': chart_data_tension_s_json,
        'chart_data_tension_d_json': chart_data_tension_d_json,
        'chart_data_glycemie_json': chart_data_glycemie_json,
    }
    
    return render(request, 'patients/patient_dashboard_overview.html', context)

### Gestion du relevé du patient

@login_required
def patient_saisie_view(request):
    """
    Affiche la page du formulaire de saisie des relevés vitaux.
    """
    context = {
        'active_page': 'saisie', # Pour mettre en surbrillance le lien dans la sidebar
        'patient_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'patients/patient_saisie_releve.html', context)

@login_required
def patient_submit_releve(request):
    """
    Traite la soumission du formulaire et enregistre un nouveau ReleveVital.
    """
    if request.method == 'POST':
        # Récupération des données du formulaire POST
        try:
            tension_systolique = int(request.POST.get('tension_systolique'))
            tension_diastolique = int(request.POST.get('tension_diastolique'))
            glycemie = float(request.POST.get('glycemie'))
            poids = request.POST.get('poids') # Peut être null/vide
            notes_patient = request.POST.get('notes_patient', '')

            # Conversion de poids en float si non vide
            poids_float = float(poids) if poids else None
            
            # Validation simple (Ajouter ici une logique de validation plus complète si nécessaire)
            if tension_systolique < 60 or tension_diastolique < 40 or glycemie < 0.5:
                 messages.error(request, "Veuillez vérifier les valeurs minimales saisies. Elles semblent trop basses.")
                 return redirect('patient_saisie_releve')
                 
            # Création et enregistrement de la nouvelle instance dans la base de données
            ReleveVital.objects.create(
                patient=request.user,
                tension_systolique=tension_systolique,
                tension_diastolique=tension_diastolique,
                glycemie=glycemie,
                poids=poids_float,
                notes_patient=notes_patient
            )
            
            messages.success(request, "Votre relevé a été enregistré avec succès et transmis à votre équipe soignante.")
            
            # Redirection vers l'aperçu du tableau de bord après succès
            return redirect('patient_dashboard') 

        except ValueError:
            messages.error(request, "Erreur de format. Veuillez entrer des nombres valides.")
            return redirect('patient_saisie_releve')
        except Exception as e:
            messages.error(request, f"Une erreur inattendue est survenue: {e}")
            return redirect('patient_saisie_releve')
            
    # Si l'accès n'est pas en POST, rediriger vers la page du formulaire
    return redirect('patient_saisie_releve')

## Fin Gestion du relevé du Patient

# Rendez-vous PAtient
@login_required
def patient_demande_rdv_view(request):
    
    """
    Affiche la page du formulaire de demande de Rendez-vous.
    """
    context = {
        'active_page': 'demande_rdv', 
        'patient_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'patients/patient_demande_rdv.html', context)


@login_required
def patient_submit_rdv(request):
    """
    Traite la soumission du formulaire et crée un nouveau RendezVous avec le statut 'P'.
    """
    if request.method == 'POST':
        try:
            date_heure_str = request.POST.get('date_heure')
            motif = request.POST.get('motif')
            notes_patient = request.POST.get('notes_patient', '')

            # 1. Validation de base : Date/Heure ne doit pas être dans le passé
            date_heure_naive = datetime.strptime(date_heure_str, '%Y-%m-%dT%H:%M')
            date_heure_demande = make_aware(date_heure_naive)
            if date_heure_demande < timezone.now():
                 messages.error(request, "La date du rendez-vous ne peut pas être dans le passé.")
                 return redirect('patient_demande_rdv')
            
            # 2. Création de l'instance RendezVous
            RendezVous.objects.create(
                patient=request.user,
                date_heure=date_heure_demande,
                motif=motif,
                # notes_internes est le champ pour le soignant, on le laisse vide ici.
                # notes_patient pourrait être ajouté au modèle si besoin, sinon on l'ignore ou on le met dans notes_internes.
                # Pour cet exemple, nous allons ignorer notes_patient si le modèle n'a pas ce champ.
                
                # STATUT PAR DÉFAUT : 'P' (Planifié/Demandé)
                statut='P' 
            )
            
            messages.success(request, f"Votre demande de RDV ({motif} le {date_heure_demande.strftime('%d/%m à %Hh%M')}) a été envoyée. Attendez la confirmation du soignant.")
            
            return redirect('patient_dashboard') 

        except ValueError:
            messages.error(request, "Erreur de format de date/heure. Veuillez réessayer.")
            return redirect('patient_demande_rdv')
        except Exception as e:
            messages.error(request, f"Une erreur inattendue est survenue: {e}")
            return redirect('patient_demande_rdv')
            
    return redirect('patient_demande_rdv')

#Fin Rendez-vous Patient

## Historique
@login_required
def patient_historique_view(request):
    """
    Affiche l'historique complet des Suivis, Rendez-vous et Relevés Vitaux du patient.
    """
    current_patient = request.user
    
    # 1. Récupération de l'historique des Suivis (du plus récent au plus ancien)
    historique_suivis = Suivi.objects.filter(
        patient=current_patient
    ).order_by('-date_suivi')

    # 2. Récupération de l'historique des Rendez-vous (tous les statuts)
    historique_rdv = RendezVous.objects.filter(
        patient=current_patient
    ).order_by('-date_heure')

    # 3. Récupération de l'historique des Relevés Vitaux (tous les enregistrements)
    historique_releves = ReleveVital.objects.filter(
        patient=current_patient
    ).order_by('-date_releve')


    context = {
        'patient_name': current_patient.get_full_name() or current_patient.username,
        'active_page': 'historique', 
        
        'historique_suivis': historique_suivis,
        'historique_rdv': historique_rdv,
        'historique_releves': historique_releves,
    }
    
    return render(request, 'patients/patient_historique.html', context)

## Paramètres et édition du profil
@login_required
def patient_parametres_view(request):
    """
    Affiche la page des paramètres personnels et médicaux du patient.
    Récupère le patient actuel et les choix de la liste déroulante (lien de parenté).
    """
    current_patient = request.user
    
    # 1. Récupération des choix pour le lien de parenté
    # On suppose que RELATION_CHOIX est défini sur le modèle Patient/User
    try:
        relation_choix = DetailsPatient.RELATION_CHOIX
    except AttributeError:
        # Si le champ n'est pas trouvé (erreur possible si le modèle n'a pas été mis à jour)
        # Ceci est un fallback simple, la définition du champ est essentielle.
        relation_choix = [] 
        
    
    context = {
        'patient_name': current_patient.get_full_name() or current_patient.username,
        'active_page': 'parametres', 
        
        # Informations de base
        'current_patient': current_patient,
        
        # Choix de la liste déroulante pour le template
        'relation_choix': relation_choix,
        
        # 'details_patient': details_patient, # Si DetailsPatient est utilisé
    }
    
    return render(request, 'patients/patient_parametres.html', context)


@login_required
def patient_update_parametres(request):
    """
    Traite la soumission du formulaire de mise à jour des informations d'urgence et de l'email du patient.
    """
    if request.method == 'POST':
        current_patient = request.user
        
        # 1. Récupération des données du formulaire POST
        nom_urgence = request.POST.get('contact_urgence_nom')
        telephone_urgence = request.POST.get('contact_urgence_telephone')
        lien_urgence = request.POST.get('contact_urgence_lien')
        email = request.POST.get('email') # <-- NOUVEAU

        try:
            # 2. Validation de l'email (simple)
            """if not email:
                 messages.error(request, "L'adresse email ne peut pas être vide.")
                 return redirect('patient_parametres')"""
                 
            # 3. Mise à jour des champs
            current_patient.contact_urgence_nom = nom_urgence
            current_patient.contact_urgence_telephone = telephone_urgence
            current_patient.contact_urgence_lien = lien_urgence
            current_patient.email = email # <-- MISE A JOUR DE L'EMAIL
            
            # 4. Sauvegarde en base de données
            current_patient.save()
            
            messages.success(request, "Vos informations ont été mises à jour avec succès (y compris l'email).")
            
            return redirect('patient_parametres') 

        except Exception as e:
            messages.error(request, f"Une erreur inattendue est survenue lors de la sauvegarde.")
            print(f"Erreur de sauvegarde: {e}")
            return redirect('patient_parametres')
            
    return redirect('patient_parametres')

## Fin Parametres 

# VUE DE DÉCONNEXION
def patient_logout_view(request):
    logout(request)
    return redirect('home') # Redirige vers la page d'accueil ou de connexion