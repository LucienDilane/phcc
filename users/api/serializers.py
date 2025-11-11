from rest_framework import serializers
from users.models import Patient, DetailsPatient
from medical_data.models import Suivi, RendezVous, ReleveVital
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password 

# Liste des clés du Serializer qui correspondent aux champs du modèle DetailsPatient
NESTED_FIELDS = [
    'taille_cm', 
    'antecedents_medicaux',
    'allergies',
    'contact_urgence_nom', 
    'contact_urgence_telephone', 
    'contact_urgence_lien',
]

RELATION_CHOIX = {
    "Conjoint(e)": "CO",
    "Parent": "PR",
    "Enfant": "EN",
    "Frère/Sœur": "FR",
    "Ami(e)": "AM",
    "Autre": "AU",
    "Non-spécifié": "AU",
    "": "AU",
}

# ----------------------------------------------------------------------
# SERIALIZER DE LECTURE/LISTE (LA BASE SANS CHAMPS DE MOT DE PASSE) 🚨 SAFE 🚨
# ----------------------------------------------------------------------
class PatientSerializer(serializers.ModelSerializer):
    """
    Sérialiseur par défaut pour la lecture et la liste (LIST/RETRIEVE). 
    """
    
    # --- 1. CHAMPS DETAILS_PATIENT (Lecture/Écriture via dotted source) ---
    taille_cm = serializers.IntegerField(source='details_dossier.taille_cm', required=False, allow_null=True)
    antecedents_medicaux = serializers.CharField(source='details_dossier.antecedents_medicaux', required=False, allow_blank=True)
    allergies = serializers.CharField(source='details_dossier.allergies', required=False, allow_blank=True)
    
    # Champ mappé pour les relevés (Assurez-vous que la méthode get_last_vital_signs existe dans cette classe)
    last_vital_signs = serializers.SerializerMethodField(read_only=True)
    
    # Champs pour le contact d'urgence
    contact_urgence_nom = serializers.CharField(source='details_dossier.contact_urgence_nom', required=False, allow_blank=True)
    contact_urgence_telephone = serializers.CharField(source='details_dossier.contact_urgence_telephone', required=False, allow_blank=True)
    contact_urgence_lien = serializers.CharField(source='details_dossier.contact_urgence_lien', required=False, allow_blank=True)
    
    def get_last_vital_signs(self, obj):
        """
        Récupère les dernières mesures de signes vitaux (ReleveVital) 
        enregistrées pour ce patient.
        """
        try:
            # Récupère le dernier ReleveVital du patient (le related_name par défaut est 'releves_vitaux')
            last_releve = obj.releves_vitaux.latest('date_releve') 
            
            # Retourne les données formatées pour l'API
            return {
                'date_releve': last_releve.date_releve.isoformat(),
                'tension_systolique': last_releve.tension_systolique,
                'tension_diastolique': last_releve.tension_diastolique,
                # Conversion des DecimalFields en float pour la sérialisation JSON
                'glycemie': float(last_releve.glycemie) if last_releve.glycemie is not None else None,
                'poids': float(last_releve.poids) if last_releve.poids is not None else None,
            }
        except ReleveVital.DoesNotExist:
            return None # Retourne None si aucun relevé n'est trouvé
        except Exception:
            return None
        
    class Meta:
        model = Patient
        fields = [
            'id', 'username',
            'first_name', 'last_name', 'email', 'adresse',
            'date_naissance', 'telephone', 'numero_urgence','groupe_sanguin',
            
            # Champs DetailsPatient
            'taille_cm', 'antecedents_medicaux', 'allergies', 
            'contact_urgence_nom', 'contact_urgence_telephone', 'contact_urgence_lien',
            'last_vital_signs'
        ]
        read_only_fields = ('id', 'username',) 
        extra_kwargs = {} # Obligatoire pour la classe enfant PatientCreateSerializer


# ----------------------------------------------------------------------
# SERIALIZER POUR LA CRÉATION DE PATIENT (Hérite de PatientSerializer)
# ----------------------------------------------------------------------
class PatientCreateSerializer(PatientSerializer):
    """
    Sérialiseur pour la création. Ajoute mot_de_passe_clair (retour) et password (entrée).
    """
    mot_de_passe_clair = serializers.CharField(read_only=True) 
    password = serializers.CharField(write_only=True, required=False) # Ajout du champ d'écriture
    
    class Meta(PatientSerializer.Meta):
        fields = PatientSerializer.Meta.fields + ['mot_de_passe_clair', 'password']
        read_only_fields = PatientSerializer.Meta.read_only_fields + ('mot_de_passe_clair',)
        extra_kwargs = PatientSerializer.Meta.extra_kwargs.copy()
        extra_kwargs.update({'password': {'write_only': True}})


    def create(self, validated_data):
        with transaction.atomic():
            details_data = validated_data.pop('details_dossier', {})
            password = validated_data.pop('password', None)

            urgence_telephone = details_data.get('contact_urgence_telephone')
            if urgence_telephone:
                validated_data['numero_urgence'] = urgence_telephone

            patient_instance_created = Patient.objects.create(**validated_data) 
            
            if password:
                patient_instance_created.set_password(password)
                patient_instance_created.save()
            
            client_lien_string = details_data.get('contact_urgence_lien', '')
            if client_lien_string:
                details_data['contact_urgence_lien'] = RELATION_CHOIX.get(client_lien_string, 'AU')
                
            DetailsPatient.objects.create(patient=patient_instance_created, **details_data)
            
            return patient_instance_created
    
# ----------------------------------------------------------------------
# SERIALIZER POUR LA MISE À JOUR (PUT/PATCH) - PatientUpdateSerializer
# ----------------------------------------------------------------------
class PatientUpdateSerializer(serializers.ModelSerializer):
    
    # Champs DetailsPatient
    taille_cm = serializers.IntegerField(source='details_dossier.taille_cm', required=False, allow_null=True)
    antecedents_medicaux = serializers.CharField(source='details_dossier.antecedents_medicaux', required=False, allow_blank=True)
    allergies = serializers.CharField(source='details_dossier.allergies', required=False, allow_blank=True)
    contact_urgence_nom = serializers.CharField(source='details_dossier.contact_urgence_nom', required=False, allow_blank=True)
    contact_urgence_telephone = serializers.CharField(source='details_dossier.contact_urgence_telephone', required=False, allow_blank=True)
    contact_urgence_lien = serializers.CharField(source='details_dossier.contact_urgence_lien', required=False, allow_blank=True, max_length=50)
    
    # Champs Patient
    date_of_birth = serializers.DateField(source='date_naissance', required=False, allow_null=True)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    telephone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    numero_urgence = serializers.CharField(required=False, allow_blank=True, max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    adresse = serializers.CharField(required=False, allow_blank=True)
    groupe_sanguin = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = Patient
        fields = (
            'id', 'first_name', 'last_name', 
            'date_of_birth', 'groupe_sanguin', 
            'telephone', 'numero_urgence', 'email', 'adresse',
            'groupe_sanguin', 'taille_cm', 
            'antecedents_medicaux', 'allergies', 
            'contact_urgence_nom', 'contact_urgence_telephone', 'contact_urgence_lien',
        )
        read_only_fields = ('id', 'username',) 

    def update(self, instance: Patient, validated_data: dict) -> Patient:
        details_data = validated_data.pop('details_dossier', {})
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        
        details_instance = instance.details_dossier 
        
        client_lien_string = details_data.get('contact_urgence_lien', '')
        if client_lien_string:
            details_data['contact_urgence_lien'] = RELATION_CHOIX.get(client_lien_string, 'AU')

        for attr, value in details_data.items():
            setattr(details_instance, attr, value)
            
        details_instance.save()
        
        return instance

# ----------------------------------------------------------------------
# SERIALIZER POUR LE RELEVE VITAL (Inchangé)
# ----------------------------------------------------------------------
class ReleveVitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleveVital
        fields = '__all__'
        read_only_fields = ['id', 'patient', 'date_releve'] 

# ----------------------------------------------------------------------
# SERIALIZER POUR LE SUIVI (Inchangé)
# ----------------------------------------------------------------------
class FollowUpSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Suivi
        fields = [
            'id', 'patient', 
            'date_suivi', 'motif', 'notes_medecin', 'prescriptions'
        ]
        read_only_fields = ['id', 'date_suivi'] 

# ----------------------------------------------------------------------
# SERIALIZER POUR LE RENDEZ-VOUS 🚨 CORRECTION read_only_fields 🚨
# ----------------------------------------------------------------------
class RendezVousSerializer(serializers.ModelSerializer):
    
    patient_full_name = serializers.SerializerMethodField(read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_phone = serializers.SerializerMethodField()

    class Meta:
        model = RendezVous
        fields = [
            'id', 'patient', 'patient_full_name', 'date_heure', 
            'motif', 'statut', 'notes_internes',
            'patient_name', 'patient_phone'
        ]
        # 🚨 CORRECTION : Les deux définitions précédentes de read_only_fields ont été fusionnées en une seule.
        read_only_fields = ('id', 'patient_full_name', 'statut', 'patient_name', 'patient_phone',) 
    
    def get_patient_name(self, obj):
        patient = obj.patient
        if patient:
            return f"{patient.first_name} {patient.last_name}"
        return "Patient inconnu"
    
    def get_patient_phone(self, obj):
        patient = obj.patient
        if patient:
            return patient.telephone
        return "N/A"

    def get_patient_full_name(self, obj):
        return obj.patient.get_full_name()