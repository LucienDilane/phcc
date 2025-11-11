from django.db import models
from django.conf import settings

class Suivi(models.Model):
    # Lien vers le patient (AUTH_USER_MODEL est notre modèle Patient)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='suivis_patient', 
        help_text="Le patient concerné par ce suivi."
    )

    # Date et heure de la consultation/observation
    date_suivi = models.DateTimeField(
        auto_now_add=True, 
        help_text="Date et heure de l'enregistrement."
    )
    
    # Informations de la Consultation
    
    motif = models.CharField(
        max_length=255, 
        null=False, 
        blank=False, 
        help_text="Motif principal de la visite."
    )
    
    notes_medecin = models.TextField(
        null=False, 
        blank=False, 
        help_text="Observations, diagnostic, et plan de soins."
    )
    
    prescriptions = models.TextField(
        blank=True, 
        null=True, 
        help_text="Détails des médicaments ou traitements prescrits (facultatif)."
    )

    class Meta:
        verbose_name = 'Suivi/Observation'
        verbose_name_plural = 'Suivis et Observations'
        # On trie les suivis du plus récent au plus ancien (pour le carnet)
        ordering = ['-date_suivi'] 

    def __str__(self):
        # Utiliser 'last_name' et 'first_name' de AbstractUser
        return f"Suivi du {self.date_suivi.strftime('%Y-%m-%d')} pour {self.patient.last_name} {self.patient.first_name}"


### MODELE DE RENDEZ-VOUS ###

class RendezVous(models.Model):
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rendez_vous',
        help_text="Le patient qui a pris le rendez-vous."
    )

    # Informations du rendez-vous
    date_heure = models.DateTimeField(
        null=False,
        blank=False,
        help_text="Date et heure prévues du rendez-vous."
    )

    # Type/motif du rendez-vous
    motif = models.CharField(
        max_length=150,
        help_text="Motif du rendez-vous (ex: consultation de routine, contrôle, etc.)."
    )

    # Statut du rendez-vous (pour le personnel)
    STATUT_CHOIX = [
        ('P', 'Planifié'),
        ('C', 'Confirmé'),
        ('A', 'Annulé'),
        ('T', 'Terminé'),
    ]
    statut = models.CharField(
        max_length=1,
        choices=STATUT_CHOIX,
        default='P',
        help_text="Statut actuel du rendez-vous."
    )
    
    # Notes internes pour le personnel (optionnel)
    notes_internes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes pour le personnel du centre (ex: préparation spéciale)."
    )

    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        # Tri des rendez-vous par date (du plus proche au plus éloigné)
        ordering = ['date_heure']

    def __str__(self):
        return f"RDV: {self.date_heure.strftime('%Y-%m-%d %H:%M')} - {self.patient.last_name}"


class ReleveVital(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='releves_vitaux',
        help_text="Le patient ayant effectué le relevé."
    )

    date_releve = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure de la saisie."
    )
    
    # 1. TENSION ARTÉRIELLE (Systolique et Diastolique)
    tension_systolique = models.IntegerField(
        null=True, blank=True,
        help_text="Tension Systolique (mmHg)."
    )
    tension_diastolique = models.IntegerField(
        null=True, blank=True,
        help_text="Tension Diastolique (mmHg)."
    )

    # 2. GLYCÉMIE (Si le patient est diabétique)
    glycemie = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Niveau de glycémie (g/L ou mmol/L)."
    )

    # 3. POIDS (Pour le suivi cardiaque ou autre)
    poids = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Poids actuel (kg)."
    )
    
    # 4. NOTES PATIENT (Optionnel)
    notes_patient = models.TextField(
        blank=True,
        help_text="Commentaires ou symptômes ressentis par le patient."
    )

    class Meta:
        verbose_name = 'Relevé Vital'
        verbose_name_plural = 'Relevés Vitaux'
        ordering = ['-date_releve'] # Du plus récent au plus ancien

    def __str__(self):
        return f"Relevé de {self.patient.username} le {self.date_releve.strftime('%d/%m/%Y à %H:%M')}"