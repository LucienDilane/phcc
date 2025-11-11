# desktop_app/patient_folder_window.py (Mise à jour Intégrale)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, 
    QDialog, QTextEdit, QFormLayout, QDialogButtonBox, QMessageBox,
    QApplication, QPushButton, QLineEdit,QComboBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont, QColor
from .utils.api_client import ApiClient 
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Définition des Couleurs Clés (Cohérentes) ---
COLOR_PRIMARY = "#2E7D32"       
COLOR_ACCENT = "#4CAF50"        
COLOR_TEXT_DARK = "#333333"     
COLOR_FOLDER_GRAY = "#607D8B"
COLOR_BACKGROUND = "#F5F5F5" 

# ---------------------------------------------------------------------
# 1. Dialogues de Détail et d'Ajout
# ---------------------------------------------------------------------

class FollowUpDetailDialog(QDialog):
    # ... (Code existant pour FollowUpDetailDialog - inchangé) ...
    # N'oubliez pas de garder ce code tel quel.
    def __init__(self, follow_up_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Détails du Suivi")
        self.setFixedSize(600, 550)
        self.follow_up_data = follow_up_data
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        title_label = QLabel(f"Suivi du {self.follow_up_data.get('date_suivi', 'N/A')[:10]}")
        title_label.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {COLOR_PRIMARY};")
        main_layout.addWidget(title_label)

        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Motif
        motif_label = QLabel(self.follow_up_data.get('motif', ''))
        motif_label.setWordWrap(True)
        form_layout.addRow(QLabel("<b>Motif de la visite:</b>"), motif_label)
        
        # Notes du médecin
        notes_editor = QTextEdit()
        notes_editor.setText(self.follow_up_data.get('notes_medecin', ''))
        notes_editor.setReadOnly(True)
        notes_editor.setStyleSheet("background-color: #FAFAFA; border: 1px solid #DDD; padding: 10px;")
        notes_editor.setMinimumHeight(200)
        form_layout.addRow(QLabel("<b>Notes & Diagnostic:</b>"), notes_editor)

        # Prescriptions
        prescriptions_editor = QTextEdit()
        prescriptions_editor.setText(self.follow_up_data.get('prescriptions', ''))
        prescriptions_editor.setReadOnly(True)
        prescriptions_editor.setStyleSheet("background-color: #FAFAFA; border: 1px solid #DDD; padding: 10px;")
        prescriptions_editor.setMinimumHeight(100)
        form_layout.addRow(QLabel("<b>Prescriptions:</b>"), prescriptions_editor)
        
        main_layout.addWidget(form_widget)

        # Bouton de Fermeture
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.clicked.connect(self.close)
        main_layout.addWidget(button_box)


class AddFollowUpDialog(QDialog):
    """Dialogue pour l'ajout d'un nouveau suivi pour un patient."""
    def __init__(self, api_client: ApiClient, patient_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data
        
        patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
        self.setWindowTitle(f"Nouveau Suivi pour {patient_name}")
        self.setFixedSize(700, 650)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # 1. Motif
        self.motif_input = QLineEdit()
        self.motif_input.setPlaceholderText("Motif principal de la consultation...")
        form_layout.addRow(QLabel("<b>Motif de la visite <span style='color: red;'>*</span>:</b>"), self.motif_input)
        
        # 2. Notes du médecin / Diagnostic
        self.notes_medecin_input = QTextEdit()
        self.notes_medecin_input.setPlaceholderText("Observations, diagnostic, plan de soins...")
        self.notes_medecin_input.setMinimumHeight(200)
        form_layout.addRow(QLabel("<b>Notes & Diagnostic <span style='color: red;'>*</span>:</b>"), self.notes_medecin_input)

        # 3. Prescriptions
        self.prescriptions_input = QTextEdit()
        self.prescriptions_input.setPlaceholderText("Détail des traitements, médicaments, conseils...")
        self.prescriptions_input.setMinimumHeight(150)
        form_layout.addRow(QLabel("<b>Prescriptions (Optionnel):</b>"), self.prescriptions_input)
        
        main_layout.addWidget(form_widget)

        # Boutons de Sauvegarde et d'Annulation
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Sauvegarder le Suivi")
        
        button_box.accepted.connect(self.accept_and_save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def accept_and_save(self):
        """Récupère les données, valide et appelle l'API pour enregistrer le suivi."""
        
        # Validation des champs obligatoires
        motif = self.motif_input.text().strip()
        notes_medecin = self.notes_medecin_input.toPlainText().strip()
        prescriptions = self.prescriptions_input.toPlainText().strip()
        
        if not motif or not notes_medecin:
            QMessageBox.warning(self, "Champs Manquants", "Le Motif de la visite et les Notes du médecin sont obligatoires.")
            return
            
        # 🚨 Préparation des données pour l'API
        follow_up_data = {
            'patient': self.patient_data.get('id'), # Clé étrangère vers le patient ID
            'motif': motif,
            'notes_medecin': notes_medecin,
            # Le champ date_suivi est auto_now_add=True sur le modèle Suivi
            'prescriptions': prescriptions if prescriptions else None,
        }

        # Appel API
        success, response_data = self.api_client.create_follow_up(follow_up_data)

        if success:
            QMessageBox.information(self, "Succès", "Nouveau suivi enregistré avec succès.")
            self.accept() # Ferme le dialogue
        else:
            error_message = response_data.get('error', 'Erreur inconnue')
            QMessageBox.critical(self, "Erreur API", f"Échec de l'enregistrement du suivi. Détails: {error_message}")
    

# ---------------------------------------------------------------------
# 2. Widgets d'Historique (Mise à jour du FollowUpHistoryWidget)
# ---------------------------------------------------------------------

class FollowUpHistoryWidget(QWidget):
    """Affiche la liste des suivis (Suivi) pour un patient."""
    def __init__(self, api_client: ApiClient, patient_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_id = patient_data.get('id')
        self.patient_data = patient_data # Ajout de patient_data pour le dialogue
        self.follow_ups_data = []
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # En-tête avec bouton "Ajouter"
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Historique des Suivis Médicaux"))
        header_layout.addStretch(1)
        
        self.add_button = QPushButton("➕ Ajouter un Suivi")
        self.add_button.setStyleSheet(f"background-color: {COLOR_ACCENT}; color: white; padding: 8px 15px; border-radius: 5px;")
        self.add_button.clicked.connect(self.open_add_follow_up_dialog)
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        # ... (Configuration du tableau - inchangée) ...
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Date du Suivi", "Motif"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_follow_up_detail)
        
        layout.addWidget(self.table)

    def load_history(self):
        """Charge l'historique des suivis depuis l'API pour ce patient."""
        # ... (Code load_history - inchangé) ...
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        response_data = self.api_client.get_follow_ups(patient_id=self.patient_id)
        QApplication.restoreOverrideCursor()

        if isinstance(response_data, list):
            self.follow_ups_data = response_data
            self.update_table()
        else:
            # 🚨 Ceci est le message qui s'affiche actuellement
            error_msg = response_data.get('error', "Impossible de charger l'historique des suivis. Vérifiez le back-end (URLs/Serializers).")
            QMessageBox.critical(self.parent(), "Erreur API", error_msg)
            self.follow_ups_data = []

    def open_add_follow_up_dialog(self):
        """Ouvre la boîte de dialogue pour ajouter un nouveau suivi."""
        dialog = AddFollowUpDialog(
            api_client=self.api_client, 
            patient_data=self.patient_data, 
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recharger l'historique après un ajout réussi
            self.load_history()

class AddRendezVousDialog(QDialog):
    """Dialogue pour planifier un nouveau rendez-vous pour un patient."""
    def __init__(self, api_client: ApiClient, patient_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data
        
        patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}"
        self.setWindowTitle(f"Planifier un Rendez-vous pour {patient_name}")
        self.setFixedSize(550, 450)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # 1. Date et Heure
        self.datetime_input = QDateTimeEdit()
        self.datetime_input.setDateTime(QDateTime.currentDateTime().addSecs(3600)) # Default to one hour later
        self.datetime_input.setCalendarPopup(True)
        form_layout.addRow(QLabel("<b>Date et Heure <span style='color: red;'>*</span>:</b>"), self.datetime_input)
        
        # 2. Motif
        self.motif_input = QLineEdit()
        self.motif_input.setPlaceholderText("Ex: Consultation de routine, bilan...")
        form_layout.addRow(QLabel("<b>Motif <span style='color: red;'>*</span>:</b>"), self.motif_input)

        # 3. Notes internes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notes pour le personnel (ex: Rappeler la veille)...")
        self.notes_input.setMinimumHeight(100)
        form_layout.addRow(QLabel("<b>Notes Internes (Optionnel):</b>"), self.notes_input)
        
        # 4. Statut Initial
        self.statut_input = QComboBox()
        # Correspond aux STATUT_CHOIX de votre models.py : ('P', 'Planifié'), ('C', 'Confirmé'), ...
        self.statut_input.addItem("Planifié", "P")
        self.statut_input.addItem("Confirmé", "C")
        # Par défaut, on ne permet pas de créer en Annulé/Terminé
        form_layout.addRow(QLabel("<b>Statut:</b>"), self.statut_input)

        main_layout.addWidget(form_widget)

        # Boutons de Sauvegarde et d'Annulation
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Save).setText("Planifier le RDV")
        
        button_box.accepted.connect(self.accept_and_save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def accept_and_save(self):
        """Récupère les données, valide et appelle l'API pour enregistrer le rendez-vous."""
        
        motif = self.motif_input.text().strip()
        
        if not motif:
            QMessageBox.warning(self, "Champs Manquants", "Le Motif du rendez-vous est obligatoire.")
            return
            
        rdv_data = {
            'patient': self.patient_data.get('id'),
            # Formater la date et l'heure au format ISO 8601 (requis par Django)
            'date_heure': self.datetime_input.dateTime().toString(Qt.DateFormat.ISODate),
            'motif': motif,
            'statut': self.statut_input.currentData(), # Récupère 'P' ou 'C'
            'notes_internes': self.notes_input.toPlainText().strip() or None,
        }

        # Appel API
        success, response_data = self.api_client.create_rendez_vous(rdv_data)

        if success:
            QMessageBox.information(self, "Succès", "Rendez-vous planifié avec succès.")
            self.accept()
        else:
            error_message = response_data.get('error', 'Erreur inconnue')
            QMessageBox.critical(self, "Erreur API", f"Échec de la planification du rendez-vous. Détails: {error_message}")