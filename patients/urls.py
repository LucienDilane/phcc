from django.urls import path
from . import views

urlpatterns = [
    # Utilisation du nom 'patient_login' et 'patient_dashboard' comme référence
    path('connexion/', views.patient_login_view, name='patient_login'),
    path('tableau-de-bord/', views.patient_dashboard_view, name='patient_dashboard'),
    path('deconnexion/', views.patient_logout_view, name='patient_logout'),
    path('historique/', views.patient_historique_view, name='patient_historique'),
    

    #### Soumission de relevé
    path('releve/saisie/', views.patient_saisie_view, name='patient_saisie_releve'),
    path('releve/submit/', views.patient_submit_releve, name='patient_submit_releve'),

    ### Rendez-vous
    path('rdv/demander/', views.patient_demande_rdv_view, name='patient_demande_rdv'),
    path('rdv/submit/', views.patient_submit_rdv, name='patient_submit_rdv'),

    ### Parametres
    path('parametres/', views.patient_parametres_view, name='patient_parametres'),
    path('parametres/update', views.patient_update_parametres, name='patient_update_parametres')
    

]