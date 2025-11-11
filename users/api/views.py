from rest_framework import viewsets,permissions,generics,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import datetime

from datetime import datetime, timedelta
# Import des modèles et sérialiseurs nécessaires
from users.models import Patient, DetailsPatient
from medical_data.models import Suivi, RendezVous,ReleveVital
from .serializers import PatientSerializer, FollowUpSerializer, RendezVousSerializer
from medical_data.api.serializers import SuiviSerializer

User = get_user_model()


class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur le modèle Patient.
    """
    # Utilisation de 'details_dossier' comme related_name
    queryset = Patient.objects.filter(is_personnel=False).select_related('details_dossier').order_by('id') 
    
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'last_name', 'first_name', 'telephone']
    
    def update(self, request, *args, **kwargs):
        """
        Gère la mise à jour des champs du Patient, 
        met à jour les Allergies et la Taille dans DetailsPatient,
        et crée une nouvelle entrée ReleveVital.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # --- Débogage pour vérifier les données reçues ---
        print(f"--- Début MAJ Patient ID: {instance.id} ---")
        print(f"Données de requête reçues: {request.data}")
        # ---------------------------------------------------

        try:
            with transaction.atomic():
                # --- 1. MISE À JOUR DES DONNÉES PATIENT PRINCIPALES (via Serializer) ---
                self.perform_update(serializer) 
                
                # --- 2. GESTION DE DETAILSPATIENT (Création si inexistant et MAJ statique/référence) ---
                
                # Récupère ou Crée l'objet DetailsPatient associé (Robustesse)
                try:
                    details = instance.details_dossier
                except DetailsPatient.DoesNotExist:
                    print(f"ATTENTION: DetailsPatient manquant pour ID {instance.id}. Création...")
                    details = DetailsPatient.objects.create(patient=instance)
                
                details_updated = False
                
                # 2a. Mise à jour de l'allergie (Champ texte)
                # CORRECTION CRITIQUE: Utilisation du nom de champ 'allergies' (vu dans serializers.py)
                if 'allergies' in request.data: 
                    allergies = request.data['allergies']
                    if details.allergies != allergies:
                        details.allergies = allergies
                        details_updated = True
                        print(f"MAJ: Allergies définies à '{allergies}'")
                        
                # 2b. Mise à jour de la taille (Champ numérique statique)
                if 'taille_cm' in request.data:
                    taille_raw = request.data['taille_cm']
                    if taille_raw is not None and str(taille_raw).strip() != '':
                        try:
                            taille = float(taille_raw)
                            if details.taille_cm != taille:
                                details.taille_cm = taille
                                details_updated = True
                                print(f"MAJ: Taille définie à {taille} cm.")
                        except (ValueError, TypeError):
                            print(f"ALERTE: Valeur de taille_cm non valide ou non numérique ignorée: {taille_raw}")
                
                if details_updated:
                    details.save()
                    print("SUCCÈS: DetailsPatient (statique) enregistré.")
                else:
                    print("INFO: Aucun champ DetailsPatient statique à mettre à jour.")
                        
                # --- 3. CRÉATION D'UN NOUVEAU RELEVÉ VITAL (Si des données vitales sont présentes) ---
                
                RELEVE_FIELDS = {
                    'tension_systolique': int, 
                    'tension_diastolique': int, 
                    'glycemie': float, 
                    'poids': float
                }
                
                releve_data = {'patient': instance}
                releve_present = False
                
                for field, target_type in RELEVE_FIELDS.items():
                    value_raw = request.data.get(field)
                    
                    if value_raw is not None and str(value_raw).strip() != '':
                        try:
                            numeric_value = target_type(value_raw)
                            releve_data[field] = numeric_value
                            releve_present = True
                            print(f"DATA RELEVE (CONVERTED): {field} = {numeric_value} ({target_type.__name__})")
                            
                        except (ValueError, TypeError):
                            print(f"ALERTE: Valeur ReleveVital non valide pour {field}: {value_raw}")
                            continue 

                if releve_present:
                    # Création du nouvel objet ReleveVital
                    ReleveVital.objects.create(**releve_data) 
                    print(f"SUCCÈS: Nouveau ReleveVital créé. (Données initiales de relevé vital enregistrées)")
                    
                    # Étape 4 (Synchronisation vers DetailsPatient) est intentionnellement RETIRÉE ici.

                else:
                    print("INFO: Aucune donnée ReleveVital à enregistrer.")


        except Exception as e:
            error_message = f"Erreur lors de l'enregistrement: {type(e).__name__}: {str(e)}"
            print(f"ERREUR ATOMIQUE: {error_message}")
            return Response({'details': error_message}, status=status.HTTP_400_BAD_REQUEST)

        # Re-sérialise l'instance complète pour le retour
        instance.refresh_from_db() 
        print("--- Fin MAJ Patient ---")
        return Response(self.get_serializer(instance).data)


    def perform_update(self, serializer):
        serializer.save()
    
# ----------------------------------------------------------------------
# ViewSets pour les données médicales (SUIVI et RENDEZ-VOUS)
# ----------------------------------------------------------------------

class SuiviViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les suivis des patients.
    Permet de filtrer les suivis par ID patient via la query parameter `?patient=<ID>`.
    """
    queryset = Suivi.objects.all().select_related('patient').order_by('-date_suivi')
    serializer_class = FollowUpSerializer 
    permission_classes = [permissions.IsAuthenticated]
    
    # 🚨 Points de Configuration CLÉS pour le filtrage :
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['patient_id'] # <-- Ceci permet de filtrer par patient ID
    # --------------------------------------------------------------------
    
    search_fields = ['patient__first_name', 'patient__last_name', 'motif', 'notes_medecin']


class RendezVousViewSet(viewsets.ModelViewSet):
    """Gère les opérations CRUD sur le modèle RendezVous."""
    
    serializer_class = RendezVousSerializer 
    permission_classes = [IsAuthenticated] 
    
    def get_queryset(self):
        # 1. Base QuerySet : Optimisation de la performance
        # Utiliser select_related pour joindre la table Patient en une seule requête SQL.
        queryset = RendezVous.objects.all().select_related('patient')
        
        # 2. Filtrage par ID Patient (pour le Dossier Patient)
        patient_id = self.request.query_params.get('patient_id')
        if patient_id is not None:
            queryset = queryset.filter(patient_id=patient_id)
            
        # 3. Filtrage par Date (pour l'Agenda)
        # Ceci vous permettra de filtrer les RDV pour une date spécifique dans l'AgendaWidget
        date_filter = self.request.query_params.get('date')
        if date_filter is not None:
           
            queryset = queryset.filter(date_heure__date=date_filter)

        return queryset.order_by('date_heure')

class CustomAuthToken(ObtainAuthToken):
    """
    Vue personnalisée pour retourner le Token et les données utilisateur lors de la connexion.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'id': user.pk,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_personnel': user.is_personnel, 
        })


class GlobalStatsView(APIView):
    """Fournit des statistiques agrégées pour le tableau de bord."""
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        try:
            # 1. Patients
            total_patients = Patient.objects.filter(is_personnel=False).count() 

            # 2. Rendez-vous (Logique RendezVous déjà corrigée)
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            
            rdv_this_week = RendezVous.objects.filter(
                date_heure__date__gte=start_of_week, 
                date_heure__date__lte=start_of_week + timedelta(days=6)
            ).count()

            # 3. Suivis (dernier mois)
            one_month_ago = timezone.now() - timedelta(days=30)
            suivis_last_month = Suivi.objects.filter(
                date_suivi__gte=one_month_ago
            ).count()

            # 🚨 CORRECTION DÉFINITIVE : Suppression de la requête 'statut' 🚨
            suivi_status_counts = [] # Retourne une liste vide au lieu de planter
            
            #4. Compte des relevés actifs (utilisant le nouveau modèle ReleveVital)
            # Ajout d'une stat pour suivre les patients actifs 
            patients_actifs_30j = ReleveVital.objects.filter(
                date_releve__gte=timezone.now() - timezone.timedelta(days=30)
            ).values('patient').annotate(num_releves=Count('patient')).count()

            return Response({
                'total_patients': total_patients,
                'rdv_this_week': rdv_this_week,
                'suivis_last_month': suivis_last_month,
                'suivi_status_counts': suivi_status_counts, # Donnée safe
                'patients_suivi_actif_30j': patients_actifs_30j,
            })
        except Exception as e:
        # Ceci garantit qu'une réponse JSON d'erreur est toujours envoyée en cas de crash
            print(f"Erreur interne lors de la récupération des statistiques: {e}") 
            return Response(
                {"error": f"Erreur interne lors de la récupération des statistiques. Détail: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )