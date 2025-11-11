from rest_framework import serializers
from medical_data.models import Suivi, RendezVous 


class FollowUpSerializer(serializers.ModelSerializer):
    # 🚨 Ajoutez ceci pour garantir que l'ID du patient est bien sérialisé
    patient_id = serializers.ReadOnlyField(source='patient.id') 

    class Meta:
        model = Suivi
        # 🚨 Utilisez la liste explicite pour éviter tout champ problématique
        fields = ['id', 'patient', 'patient_id', 'date_suivi', 'motif', 'notes_medecin', 'prescriptions']

class RendezVousSerializer(serializers.ModelSerializer):
    # 🚨 Ajoutez ceci pour garantir que l'ID du patient est bien sérialisé
    patient_id = serializers.ReadOnlyField(source='patient.id') 

    class Meta:
        model = RendezVous
        fields = ['id', 'patient', 'patient_id', 'date_heure', 'motif', 'statut', 'notes_internes']

class SuiviSerializer(serializers.ModelSerializer):
    # Nous utilisons 'patient__first_name' car le FK pointe vers le modèle utilisateur
    patient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Suivi 
        fields = '__all__' 
        # Si vous utilisez la pagination, l'ID du patient est crucial pour le filtrage
    
    def get_patient_name(self, obj):
        # Utiliser les champs du modèle utilisateur/patient
        return f"{obj.patient.first_name} {obj.patient.last_name}"