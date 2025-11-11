from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.contrib.auth.hashers import make_password
from django.conf import settings
import random
import string
import uuid

class Patient(AbstractUser):
    
    # Gestionnaire d'utilisateurs
    objects = UserManager() 
    
    # Variable pour stocker le mot de passe clair AVANT hachage
    mot_de_passe_clair = None 
    
    # --- Champs OBLIGATOIRES SPÉCIFIQUES ---
    
    # 1. Numéro du Patient (ID unique et généré par défaut)
    numero_patient = models.CharField(
        max_length=50, 
        unique=True, 
        default=uuid.uuid4, # Utilise un UUID comme valeur par défaut
        help_text="Identifiant unique du patient."
    )
    
    # 2. Numéro de Téléphone principal (Obligatoire)
    telephone = models.CharField(max_length=20, null=False, blank=False)
    
    # 3. Numéro de Téléphone d'Urgence (Obligatoire)
    numero_urgence = models.CharField(max_length=20, null=True, blank=True)

    # --- Autres Champs (Facultatifs ou personnalisés) ---
    
    email = models.EmailField(blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    
    # Choix du groupe sanguin
    GROUPE_SANGUIN_CHOIX = [
        ('A+', 'A positif'), ('A-', 'A négatif'),
        ('B+', 'B positif'), ('B-', 'B négatif'),
        ('AB+', 'AB positif'), ('AB-', 'AB négatif'),
        ('O+', 'O positif'), ('O-', 'O négatif'),
    ]
    groupe_sanguin = models.CharField(
        max_length=3,
        choices=GROUPE_SANGUIN_CHOIX,
        blank=True,
        null=True
    )
    
    # Indicateur pour différencier le personnel des patients si nécessaire
    is_personnel = models.BooleanField(default=False)

    def generate_simple_password(self, length=7):
        # On utilise des lettres minuscules et des chiffres
        characters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(characters) for i in range(length))

    # Logique de sauvegarde pour la génération du mot de passe et du username
    def save(self, *args, **kwargs):
        
        # Flag pour savoir si c'est une nouvelle création (pas encore d'ID)
        is_new = not self.pk
        
        # 1. GESTION DU MOT DE PASSE (Seulement lors de la création ou si non haché)
        if is_new or not self.password.startswith(('pbkdf2', 'bcrypt')):
            # Génère et stocke le mot de passe en clair (pour l'affichage client)
            self.mot_de_passe_clair = self.generate_simple_password(length=7) 
            # Hache le mot de passe avant de le stocker
            self.password = make_password(self.mot_de_passe_clair)
            
        # 2. PREMIÈRE SAUVEGARDE (Crée l'ID self.pk)
        super().save(*args, **kwargs)

        # 3. GESTION DU USERNAME (Après la première sauvegarde pour obtenir l'ID)
        if is_new:
            # Format: PAT-0000X. On utilise self.pk qui est désormais disponible
            new_username = f"PAT-{self.pk:05d}" 
            
            # Vérifie si le username généré est différent de l'actuel
            if self.username != new_username:
                self.username = new_username
                # ⚠️ Deuxième sauvegarde pour mettre à jour le username
                kwargs.pop('force_insert', None)
                kwargs.pop('force_update', None)
                super().save(update_fields=['username'], *args, **kwargs)


    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def __str__(self):
        # Affiche le nom, prénom et numéro de patient
        return f"Patient {self.numero_patient} : {self.first_name} {self.last_name}"


class DetailsPatient(models.Model):
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='details_dossier',
        help_text="Lien unique vers le compte utilisateur (patient)."
    )
    
    # 1. ANTÉCÉDENTS ET ALLERGIES (Critique)
    
    antecedents_medicaux = models.TextField(
        blank=True,
        null=True,
        help_text="Historique des maladies chroniques, chirurgies majeures, hospitalisations."
    )
    
    allergies = models.TextField(
        blank=True,
        null=True,
        help_text="Allergies médicamenteuses ou alimentaires (CRITIQUE)."
    )

    taille_cm = models.IntegerField(
        null=True, blank=True,
        help_text="Taille du patient (cm)."
    )
    
    # 3. CONTACT D'URGENCE (Critique pour les soignants)
    
    # 🚨 Choix pour le lien de parenté/relation
    RELATION_CHOIX = [
        ('PR', 'Parent'),
        ('CO', 'Conjoint(e)'),
        ('EN','Enfant'),
        ('FR','Frère/Soeur'),
        ('AM', 'Ami(e)'),
        ('AU', 'Autre'),
    ]


    contact_urgence_nom = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nom complet de la personne à contacter en cas d'urgence"
    )
    contact_urgence_telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Téléphone de la personne à contacter en cas d'urgence"
    )
    contact_urgence_lien = models.CharField(
        max_length=2,
        choices=RELATION_CHOIX,
        default='AU',
        verbose_name="Lien de parenté ou relation",
        help_text="Spécifiez le lien entre vous et cette personne."
    )

    class Meta:
        verbose_name = 'Détail Patient'
        verbose_name_plural = 'Détails Patients'

    def __str__(self):
        # Assurez-vous que get_full_name() ou username est disponible sur settings.AUTH_USER_MODEL
        return f"Détails Cliniques de {self.patient.get_full_name() or self.patient.username}"
    