# desktop_app/add_patient_dialog.py (Intégral avec Saisie de Nouveau Relevé Vital)

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QMessageBox, QComboBox, 
    QTextEdit, QSpinBox, QDoubleSpinBox, QWidget, QDateEdit, 
    QSizePolicy, QTabWidget, QGroupBox 
)
from PyQt6.QtCore import Qt, QDate 
from .utils.api_client import ApiClient 
import json 
import logging
from datetime import datetime 

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# --- Définition des Couleurs Clés ---
COLOR_MAIN_GREEN = "#4CAF50"
COLOR_DARK_GREEN = "#388E3C"
COLOR_DANGER_RED = "#D32F2F"
COLOR_ACCENT_BLUE = "#2196F3" 

class AddPatientDialog(QDialog):
    GROUPE_SANGUIN_CHOICES = ["A+", "A-", "B+", "B-", "AB+", "AB-\t", "O+", "O-", "Inconnu"]
    RELATION_CHOIX = ["Conjoint(e)", "Parent", "Enfant", "Frère/Sœur", "Ami(e)", "Autre", "Non-spécifié"]
    
    # Mappages désormais inutilisés mais conservés pour référence de la structure passée
    REFERENCE_TO_LAST_MEASURE = {
        'poids_initial': 'poids',
        'tension_reference_systolique': 'tension_systolique',
        'tension_reference_diastolique': 'tension_diastolique',
        'glycemie_reference': 'glycemie'
    }
    
    def __init__(self, api_client: ApiClient, patient_data=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data if patient_data else {}
        self.is_edit_mode = bool(patient_data)
        
        self.initial_measure_values = {} 
        
        self.widgets = {} # Contient tous les QLineEdit, QSpinBox, QLabel etc.
        self._setup_ui()
        self._apply_styles()
        
        if self.is_edit_mode:
            self._load_patient_data()
            self.setWindowTitle(f"Éditer Patient: {self.patient_data.get('first_name', '')} {self.patient_data.get('last_name', '')}")
        else:
            self.setWindowTitle("Ajouter un Nouveau Patient")
            
            
    def _apply_styles(self):
        """Applique des styles CSS pour l'apparence de la boîte de dialogue."""
        self.setStyleSheet(f"""
            QDialog {{ background-color: #f7f9fc; }}
            QLabel {{ font-size: 14px; color: #333; }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
                padding: 8px; border: 1px solid #ccc; border-radius: 6px; background-color: white; font-size: 14px;
            }}
            .ReferenceValueLabel {{
                font-weight: bold; color: #000; padding: 8px; border: 1px solid #eee; 
                border-radius: 6px; background-color: #f0f0f0; min-height: 14px; vertical-align: middle;
            }}
            QPushButton {{
                padding: 10px 20px; border: none; border-radius: 8px; font-weight: bold;
                font-size: 14px; min-width: 100px;
            }}
            #SaveButton {{ background-color: {COLOR_MAIN_GREEN}; color: white; }}
            #SaveButton:hover {{ background-color: {COLOR_DARK_GREEN}; }}
            #CancelButton {{ background-color: #e0e0e0; color: #333; }}
            #CancelButton:hover {{ background-color: #bdbdbd; }}
            QTabWidget::pane {{ border: 1px solid #ccc; background-color: white; border-radius: 8px; }}
            QTabBar::tab {{
                background: #f0f0f0; color: #555; padding: 10px 15px; border-top-left-radius: 8px;
                border-top-right-radius: 8px; border: 1px solid #ccc; margin-right: 2px;
            }}
            QTabBar::tab:selected {{ background: white; color: {COLOR_DARK_GREEN}; border-bottom-color: white; }}
            QGroupBox {{
                font-weight: bold; font-size: 15px; margin-top: 10px; border: 1px solid #ddd;
                border-radius: 8px; padding-top: 20px;
            }}
            .LastReleveLabel {{ font-style: italic; color: #666; font-size: 12px; }}
            .LastReleveValue {{ font-weight: bold; color: {COLOR_ACCENT_BLUE}; font-size: 14px; }}
        """)

    def _setup_ui(self):
        """Initialise la mise en page principale et les onglets."""
        main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.civil_page = QWidget()
        self.medical_page = QWidget()
        self.antecedents_page = QWidget()

        self.tab_widget.addTab(self.civil_page, "Infos Civiles")
        self.tab_widget.addTab(self.medical_page, "Infos Médicales & Vitals")
        self.tab_widget.addTab(self.antecedents_page, "Antécédents & Urgence")
        
        self._setup_civil_page()
        self._setup_medical_page()
        self._setup_antecedents_page()
        
        control_layout = QHBoxLayout()
        control_layout.addStretch(1)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.setObjectName("CancelButton")
        cancel_button.clicked.connect(self.reject)
        control_layout.addWidget(cancel_button)
        
        save_button = QPushButton("Enregistrer")
        save_button.setObjectName("SaveButton")
        save_button.clicked.connect(self._save_patient)
        control_layout.addWidget(save_button)
        
        main_layout.addLayout(control_layout)

    def _setup_civil_page(self):
        """Configure l'onglet Informations Civiles."""
        form_layout = QFormLayout(self.civil_page)
        form_layout.setSpacing(15)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.widgets['last_name'] = QLineEdit()
        self.widgets['first_name'] = QLineEdit()
        self.widgets['date_naissance'] = QDateEdit()
        self.widgets['date_naissance'].setCalendarPopup(True)
        self.widgets['date_naissance'].setDate(QDate.currentDate().addYears(-30)) 
        self.widgets['date_naissance'].setDisplayFormat("dd/MM/yyyy")
        self.widgets['gender'] = QComboBox()
        self.widgets['gender'].addItems(["Femme", "Homme", "Autre", "Non-spécifié"])
        self.widgets['telephone'] = QLineEdit()
        self.widgets['email'] = QLineEdit()
        self.widgets['adresse'] = QTextEdit()
        self.widgets['adresse'].setFixedHeight(70)

        form_layout.addRow("Nom (*)", self.widgets['last_name'])
        form_layout.addRow("Prénom (*)", self.widgets['first_name'])
        form_layout.addRow("Date de Naissance", self.widgets['date_naissance'])
        form_layout.addRow("Sexe", self.widgets['gender'])
        form_layout.addRow("Téléphone", self.widgets['telephone'])
        form_layout.addRow("Email", self.widgets['email'])
        form_layout.addRow("Adresse", self.widgets['adresse'])


    def _setup_medical_page(self):
        """Configure l'onglet Informations Médicales et Vitales."""
        main_layout = QVBoxLayout(self.medical_page)
        
        # 1. Infos de base 
        base_group = QGroupBox("Informations de base")
        base_form = QFormLayout(base_group)
        base_form.setSpacing(15)
        base_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        base_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.widgets['groupe_sanguin'] = QComboBox()
        self.widgets['groupe_sanguin'].addItems(self.GROUPE_SANGUIN_CHOICES)
        base_form.addRow("Groupe Sanguin", self.widgets['groupe_sanguin'])

        self.widgets['taille_cm'] = QSpinBox()
        self.widgets['taille_cm'].setRange(0, 300)
        self.widgets['taille_cm'].setSuffix(" cm")
        base_form.addRow("Taille", self.widgets['taille_cm'])
        
        main_layout.addWidget(base_group)
        
        # 2. Groupe Dernier Relevé Enregistré (Lecture Seule)
        last_vitals_group = QGroupBox("Dernier Relevé Enregistré")
        last_vitals_layout = QFormLayout(last_vitals_group)
        last_vitals_layout.setSpacing(10)
        
        self.widgets['display_last_poids'] = QLabel("N/A")
        self.widgets['display_last_poids'].setProperty("class", "LastReleveValue")
        
        self.widgets['display_last_tension'] = QLabel("N/A")
        self.widgets['display_last_tension'].setProperty("class", "LastReleveValue")
        
        self.widgets['display_last_glycemie'] = QLabel("N/A")
        self.widgets['display_last_glycemie'].setProperty("class", "LastReleveValue")

        self.widgets['display_last_releve_date'] = QLabel("N/A")
        self.widgets['display_last_releve_date'].setProperty("class", "LastReleveLabel")
        
        last_vitals_layout.addRow("Date du relevé:", self.widgets['display_last_releve_date'])
        last_vitals_layout.addRow("Poids:", self.widgets['display_last_poids'])
        last_vitals_layout.addRow("Tension:", self.widgets['display_last_tension'])
        last_vitals_layout.addRow("Glycémie:", self.widgets['display_last_glycemie'])

        main_layout.addWidget(last_vitals_group)
        
        
        # 3. NOUVEAU GROUPE : Saisie de Relevés Actuels (ÉDITABLE)
        new_vitals_group = QGroupBox("Nouveau Relevé Actuel (Saisie)")
        new_vitals_layout = QFormLayout(new_vitals_group)
        new_vitals_layout.setSpacing(10)

        # Champs éditables
        self.widgets['new_poids'] = QDoubleSpinBox()
        self.widgets['new_poids'].setSuffix(" kg")
        self.widgets['new_poids'].setRange(0.0, 300.0)
        self.widgets['new_poids'].setDecimals(2)
        self.widgets['new_poids'].setSpecialValueText("0.00 (Non saisi)")

        self.widgets['new_tension_systolique'] = QSpinBox()
        self.widgets['new_tension_systolique'].setSuffix(" mmHg")
        self.widgets['new_tension_systolique'].setRange(0, 300)
        self.widgets['new_tension_systolique'].setSpecialValueText("0 (Non saisi)")

        self.widgets['new_tension_diastolique'] = QSpinBox()
        self.widgets['new_tension_diastolique'].setSuffix(" mmHg")
        self.widgets['new_tension_diastolique'].setRange(0, 300)
        self.widgets['new_tension_diastolique'].setSpecialValueText("0 (Non saisi)")
        
        self.widgets['new_glycemie'] = QDoubleSpinBox()
        self.widgets['new_glycemie'].setSuffix(" g/L")
        self.widgets['new_glycemie'].setRange(0.0, 20.0)
        self.widgets['new_glycemie'].setDecimals(2)
        self.widgets['new_glycemie'].setSpecialValueText("0.00 (Non saisi)")
        
        new_vitals_layout.addRow("Poids actuel:", self.widgets['new_poids'])
        new_vitals_layout.addRow("Tension Systolique:", self.widgets['new_tension_systolique'])
        new_vitals_layout.addRow("Tension Diastolique:", self.widgets['new_tension_diastolique'])
        new_vitals_layout.addRow("Glycémie actuelle:", self.widgets['new_glycemie'])
        
        main_layout.addWidget(new_vitals_group)
        main_layout.addStretch(1)


    def _setup_antecedents_page(self):
        """Configure l'onglet Antécédents et Urgence."""
        main_layout = QVBoxLayout(self.antecedents_page)
        
        # 1. Groupe Antécédents 
        antecedents_group = QGroupBox("Antécédents Médicaux et Allergies")
        antecedents_layout = QFormLayout(antecedents_group)
        
        antecedents_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        antecedents_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.widgets['antecedents_medicaux'] = QTextEdit()
        self.widgets['antecedents_medicaux'].setPlaceholderText("Historique des maladies, opérations, conditions chroniques...")
        self.widgets['antecedents_medicaux'].setFixedHeight(100)
        antecedents_layout.addRow("Antécédents", self.widgets['antecedents_medicaux'])
        
        self.widgets['allergies'] = QTextEdit()
        self.widgets['allergies'].setPlaceholderText("Liste des allergies (médicaments, aliments, environnement)...")
        self.widgets['allergies'].setFixedHeight(70)
        antecedents_layout.addRow("Allergies", self.widgets['allergies'])
        
        main_layout.addWidget(antecedents_group)
        
        # 2. Groupe Contact d'Urgence 
        urgence_group = QGroupBox("Contact d'Urgence")
        urgence_form = QFormLayout(urgence_group)
        
        urgence_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        urgence_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        self.widgets['contact_urgence_nom'] = QLineEdit()
        self.widgets['contact_urgence_telephone'] = QLineEdit()
        
        self.widgets['contact_urgence_lien'] = QComboBox()
        self.widgets['contact_urgence_lien'].addItems(self.RELATION_CHOIX)
        
        urgence_form.addRow("Nom Complet", self.widgets['contact_urgence_nom'])
        urgence_form.addRow("Téléphone", self.widgets['contact_urgence_telephone'])
        urgence_form.addRow("Lien de Parenté", self.widgets['contact_urgence_lien'])
        
        main_layout.addWidget(urgence_group)
        main_layout.addStretch(1)


    def _load_patient_data(self):
        """
        Charge les données du patient et affiche le dernier relevé vital.
        """
        if not self.patient_data:
            return

        data_to_load = self.patient_data.copy()
        
        # 🚨 Récupérer le dictionnaire imbriqué last_vital_signs 🚨
        latest_vitals = self.patient_data.get('last_vital_signs', {})
        
        last_poids = latest_vitals.get('poids')
        last_systolic = latest_vitals.get('tension_systolique')
        last_diastolic = latest_vitals.get('tension_diastolique')
        last_glycemie = latest_vitals.get('glycemie')
        last_date = latest_vitals.get('date_releve')
        
        # 1. Chargement des Widgets Editables/Labels non vitaux
        for key, widget in self.widgets.items():
            
            # On ignore tous les champs vitaux (nouveaux et affichage lecture seule)
            if key.startswith(('new_', 'display_')):
                
                # S'assurer que les champs de Saisie de Nouveau Relevé sont réinitialisés à 0
                if key in ['new_poids', 'new_tension_systolique', 'new_tension_diastolique', 'new_glycemie']:
                    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                        widget.setValue(0)
                continue

            value = data_to_load.get(key)
            
            # Gestion des valeurs None/vide
            if value is None or (isinstance(value, str) and value.strip() == ""):
                if isinstance(widget, QSpinBox):
                    widget.setValue(0) 
                elif isinstance(widget, QComboBox):
                    index = widget.findText("Non-spécifié")
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    else:
                        widget.setCurrentIndex(0)
                continue

            try:
                if isinstance(widget, QLineEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QTextEdit):
                    widget.setText(str(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                    else:
                         widget.setCurrentIndex(0) 

                elif isinstance(widget, QDateEdit):
                    qdate = QDate.fromString(str(value), "yyyy-MM-dd")
                    if qdate.isValid():
                        widget.setDate(qdate)
                
                elif isinstance(widget, QSpinBox):
                    final_val = int(value) if isinstance(value, float) else value
                    if isinstance(final_val, int) and final_val >= widget.minimum() and final_val <= widget.maximum():
                        widget.setValue(final_val)

            except Exception as e:
                logger.error(f"Erreur de chargement pour le champ '{key}' avec la valeur '{value}' et le widget '{type(widget)}': {e}")
                
        # 2. Chargement des dernières mesures vitales (Lecture Seule)

        # Poids
        poids_value = float(last_poids) if isinstance(last_poids, (float, int)) and last_poids is not None else None
        poids_text = f"{poids_value:.2f} kg" if poids_value is not None and poids_value > 0 else "Aucun relevé"
        self.widgets['display_last_poids'].setText(poids_text)
            
        # Tension
        tension_text = "Aucun relevé"
        if isinstance(last_systolic, int) and isinstance(last_diastolic, int) and last_systolic is not None and last_systolic > 0:
            tension_text = f"{last_systolic}/{last_diastolic} mmHg"
        self.widgets['display_last_tension'].setText(tension_text)
            
        # Glycémie
        glycemie_value = float(last_glycemie) if isinstance(last_glycemie, (float, int)) and last_glycemie is not None else None
        glycemie_text = f"{glycemie_value:.2f} g/L ou mmol/L" if glycemie_value is not None and glycemie_value > 0 else "Aucun relevé"
        self.widgets['display_last_glycemie'].setText(glycemie_text)

        # Date
        date_text = "N/A"
        if last_date:
            try:
                # Le format attendu du Serializer est 'YYYY-MM-DD HH:MM:SS'
                dt_obj = datetime.strptime(str(last_date).split('.')[0].replace('T', ' '), '%Y-%m-%d %H:%M:%S') 
                date_text = dt_obj.strftime("Le %d/%m/%Y à %H:%M")
            except Exception:
                date_text = str(last_date).split('T')[0] 
        
        self.widgets['display_last_releve_date'].setText(date_text)


    def _collect_patient_data(self):
        """
        Collecte les données du patient (éditables) et fusionne les nouvelles mesures vitales
        en utilisant les clés attendues par le backend ('poids', 'tension_systolique', ...).
        """
        data = {}
        
        # Collecte de TOUTES les données (patient + nouvelles mesures)
        for key, widget in self.widgets.items():
            
            # --- Champs de saisie de Nouvelles Mesures Vitales 🚨 ---
            if key.startswith('new_'):
                value = None
                if isinstance(widget, QSpinBox):
                    value = widget.value()
                elif isinstance(widget, QDoubleSpinBox):
                    value = widget.value()
                
                # N'enregistre que si une valeur significative a été saisie (> 0)
                if value is not None and value > 0:
                    model_field = key.replace('new_', '') 
                    
                    # Le backend gère la conversion, mais on envoie un type cohérent
                    if model_field in ['poids', 'glycemie']:
                         data[model_field] = float(value)
                    elif model_field in ['tension_systolique', 'tension_diastolique']:
                         data[model_field] = int(value)
                
            # --- Autres champs (Editables) ---
            else:
                value = None
                if isinstance(widget, QLineEdit):
                    value = widget.text().strip()
                elif isinstance(widget, QTextEdit):
                    value = widget.toPlainText().strip()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                    # Convertit le "Non-spécifié" pour l'API si le champ est le lien d'urgence
                    if key == 'contact_urgence_lien' and value == "Non-spécifié":
                        value = ""
                elif isinstance(widget, QDateEdit):
                    value = widget.date().toString("yyyy-MM-dd")
                elif isinstance(widget, QSpinBox):
                    value = widget.value()
                    
                
                # N'inclut que les champs non-Label et non-DoubleSpinBox
                if not isinstance(widget, (QLabel, QDoubleSpinBox)) and value is not None and (value != "" or key == 'contact_urgence_lien'): 
                    data[key] = value

        return data


    def _save_patient(self):
        """
        Appelle l'API pour mettre à jour les données du patient. Les nouvelles mesures vitales
        sont incluses dans la requête et traitées par le backend (views.py) pour créer un nouveau ReleveVital.
        """
        # data_to_save contient les données du patient ET les nouvelles mesures vitales
        data_to_save = self._collect_patient_data()
        patient_id = self.patient_data.get('id') if self.is_edit_mode else None
        
        if not data_to_save.get('first_name') or not data_to_save.get('last_name'):
            QMessageBox.warning(self, "Champs Manquants", "Veuillez saisir le prénom et le nom du patient (champs obligatoires).")
            return

        # 1. Mise à jour ou Création du Patient
        if self.is_edit_mode:
            # Envoie la requête unique contenant les infos patient ET les nouvelles mesures vitales
            success, response_data, status_code = self.api_client.update_patient(patient_id, data_to_save)
        else:
            success, response_data, status_code = self.api_client.create_patient(data_to_save)

        if not success:
            details = response_data.get('details', response_data.get('error', 'Aucun détail fourni par la connexion.'))
            
            # Tentative d'affichage des erreurs détaillées JSON du serveur
            details_display = details
            try:
                 if isinstance(response_data, dict):
                    details_display = json.dumps(response_data, indent=4, ensure_ascii=False)
                 elif isinstance(details, str):
                    details_display = json.dumps(json.loads(details), indent=4, ensure_ascii=False)
            except Exception:
                 pass
                 
            QMessageBox.critical(self, "Erreur d'Enregistrement", 
                                 f"Échec de l'opération.\n\nErreurs détaillées du serveur :\n{details_display}")
            return
            
        self.patient_data = response_data
        
        # 2. Message de succès
        if not self.is_edit_mode:
            username_generated = response_data.get('username', 'N/A') 
            mdp_clair = response_data.get('mot_de_passe_clair', 'Non reçu')

            QMessageBox.information(self, "SUCCÈS", 
                                    f"Patient enregistré avec succès.\n"
                                    f"Login: **{username_generated}**\n"
                                    f"Mot de passe temporaire: **{mdp_clair}**\n"
                                    f"Ces informations doivent être notées dans le carnet du patient.",
                                    QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "SUCCÈS", "Modifications enregistrées avec succès.", QMessageBox.StandardButton.Ok)
            
        self.accept()