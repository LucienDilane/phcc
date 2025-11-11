from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, 
    QDialog, QTextEdit, QFormLayout, QDialogButtonBox, QMessageBox,
    QApplication, QGroupBox, QPushButton,QComboBox, QLineEdit, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from .utils.api_client import ApiClient 
import logging
import datetime
from datetime import datetime, timezone


logger = logging.getLogger(__name__)

# --- Définition des Couleurs Clés (Cohérentes) ---
COLOR_PRIMARY = "#2E7D32"       
COLOR_ACCENT = "#4CAF50"        
COLOR_TEXT_DARK = "#333333"     
COLOR_FOLDER_GRAY = "#607D8B"
COLOR_BACKGROUND = "#F5F5F5" 

# ---------------------------------------------------------------------
# 1. Dialogues de Détail
# ---------------------------------------------------------------------

class FollowUpDetailDialog(QDialog):
    """Affiche les détails complets d'un suivi sélectionné."""
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


# ---------------------------------------------------------------------
# 2. Widgets d'Historique
# ---------------------------------------------------------------------

class FollowUpHistoryWidget(QWidget):
    """Affiche la liste des suivis (Suivi) pour un patient."""
    def __init__(self, api_client: ApiClient, patient_id: int, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_id = patient_id
        self.follow_ups_data = []
        self.init_ui()
        self.load_history()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Date du Suivi", "Motif"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Motif prend l'espace restant
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_follow_up_detail)
        
        layout.addWidget(self.table)

    def load_history(self):
        """Charge l'historique des suivis depuis l'API pour ce patient."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        # 🚨 Appel API supposé : /api/suivis/?patient_id=X
        response_data = self.api_client.get_follow_ups(patient_id=self.patient_id)
        QApplication.restoreOverrideCursor()

        if isinstance(response_data, list):
            self.follow_ups_data = response_data
            self.update_table()
        else:
            QMessageBox.critical(self.parent(), "Erreur API", "Impossible de charger l'historique des suivis.")
            self.follow_ups_data = []

    def update_table(self):

       
        """Met à jour le tableau avec les données de suivi."""
        self.table.setRowCount(len(self.follow_ups_data))
        
        for row, fu in enumerate(self.follow_ups_data):
            
            # ID (masqué ou non, utile pour le référencement)
            item_id = QTableWidgetItem(str(fu.get('id', 'N/A')))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_id)
            
            # Date (formatée)
            date_str = fu.get('date_suivi', 'N/A')
            try:
                # Formatage de la date (ex: 2023-10-25 14:30)
                dt = QDateTime.fromString(date_str, Qt.DateFormat.ISODate)
                formatted_date = dt.toString("yyyy-MM-dd hh:mm")
            except:
                formatted_date = date_str[:16].replace('T', ' ')
            
            item_date = QTableWidgetItem(formatted_date)
            self.table.setItem(row, 1, item_date)

            # Motif
            item_motif = QTableWidgetItem(fu.get('motif', 'N/A'))
            self.table.setItem(row, 2, item_motif)
            
        self.table.hideColumn(0) # On peut cacher l'ID

    def open_follow_up_detail(self):
        """Ouvre la boîte de dialogue pour afficher les détails d'un suivi."""
        selected_rows = self.table.selectedIndexes()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        detail_data = self.follow_ups_data[row]
        
        dialog = FollowUpDetailDialog(detail_data, parent=self)
        dialog.exec()

#------------------------------------------------------------------
        #Classes de rendez-vous
#------------------------------------------------------------------

class AddRendezVousDialog(QDialog):
    """Dialogue pour planifier un nouveau rendez-vous pour un patient."""
    def __init__(self, api_client, patient_data: dict, existing_rdv_data: dict = None, parent=None,default_datetime=None): 
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data
        self.existing_rdv_data = existing_rdv_data # 🚨 Stocker les données si mode édition
        self.default_datetime = default_datetime
        
        patient_name = f"{patient_data.get('first_name', '')} {patient_data.get('last_name', 'Patient')}"
        
        if self.existing_rdv_data:
            self.setWindowTitle(f"Modifier Rendez-vous pour {patient_name}")
        else:
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
        
            # 1. Afficher l'heure en plus de la date pour faciliter la modification.
        self.datetime_input.setDisplayFormat("dd/MM/yyyy HH:mm") 
        
            # 2. Permettre la modification des champs de date/heure par défilement (spin box)
        self.datetime_input.setDisplayFormat("dd/MM/yyyy HH:mm") 
        
            # 3. Mode édition : permet de sélectionner et modifier le jour, le mois, l'année, l'heure, les minutes.
        self.datetime_input.setCalendarPopup(True) # Garder le calendrier pour la modification de date
        
             # 🚨 Pré-remplissage 🚨
        if self.existing_rdv_data and self.existing_rdv_data.get('date_heure'):
            dt_from_db = QDateTime.fromString(self.existing_rdv_data['date_heure'], Qt.DateFormat.ISODate)
            self.datetime_input.setDateTime(dt_from_db)

        elif self.default_datetime:
            self.datetime_input.setDateTime(self.default_datetime)
        else:
            self.datetime_input.setDateTime(QDateTime.currentDateTime().addSecs(3600)) 
        
        self.datetime_input.setCalendarPopup(True) 
        
        form_layout.addRow(QLabel("<b>Date et Heure <span style='color: red;'>*</span>:</b>"), self.datetime_input)
        
        # 2. Motif
        self.motif_input = QLineEdit()
        # 🚨 Pré-remplissage 🚨
        if self.existing_rdv_data:
            self.motif_input.setText(self.existing_rdv_data.get('motif', ''))
            
        self.motif_input.setPlaceholderText("Ex: Consultation de routine, bilan...")
        form_layout.addRow(QLabel("<b>Motif <span style='color: red;'>*</span>:</b>"), self.motif_input)

        # 3. Notes internes
        self.notes_input = QTextEdit()
        # 🚨 Pré-remplissage 🚨
        if self.existing_rdv_data and self.existing_rdv_data.get('notes_internes'):
            self.notes_input.setText(self.existing_rdv_data['notes_internes'])
            
        self.notes_input.setPlaceholderText("Notes pour le personnel (ex: Rappeler la veille)...")
        self.notes_input.setMinimumHeight(100)
        form_layout.addRow(QLabel("<b>Notes Internes (Optionnel):</b>"), self.notes_input)
        
        # 4. Statut Initial
        self.statut_input = QComboBox()
        self.statut_input.addItem("Planifié", "P") 
        self.statut_input.addItem("Confirmé", "C") 
        
        # 🚨 Pré-sélection du statut si mode édition 🚨
        if self.existing_rdv_data:
            index = self.statut_input.findData(self.existing_rdv_data.get('statut', 'P'))
            if index != -1:
                self.statut_input.setCurrentIndex(index)
            # Ne pas permettre la modification de statut en T ou A ici
            if self.existing_rdv_data.get('statut') in ['A', 'T']:
                self.statut_input.setEnabled(False) 
            
        form_layout.addRow(QLabel("<b>Statut:</b>"), self.statut_input)

        main_layout.addWidget(form_widget)

        # Boutons de Sauvegarde et d'Annulation
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        
        # 🚨 Texte du bouton selon le mode 🚨
        save_text = "Modifier le RDV" if self.existing_rdv_data else "Planifier le RDV"
        button_box.button(QDialogButtonBox.StandardButton.Save).setText(save_text)
        
        button_box.accepted.connect(self.accept_and_save)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        

    def accept_and_save(self):
        """Récupère les données, valide et appelle l'API (création ou modification)."""
        
        # 🚨 1. RÉCUPÉRATION DU MOTIF ET VALIDATION 🚨
        motif = self.motif_input.text().strip()
        
        if not motif:
            QMessageBox.warning(self, "Champs Manquants", "Le Motif du rendez-vous est obligatoire.")
            return

        # 2. Validation de la date future (seulement pour la CRÉATION ou la MODIFICATION d'une date future)
        selected_qdatetime = self.datetime_input.dateTime()
        
        current_datetime = datetime.now() 
        selected_datetime = datetime.fromtimestamp(selected_qdatetime.toSecsSinceEpoch())

        # On ne bloque la date passée que si le RDV est Planifié/Confirmé
        if self.existing_rdv_data is None or self.existing_rdv_data.get('statut') in ['P', 'C']:
            if selected_datetime < current_datetime:
                QMessageBox.warning(self, "Erreur de Date", 
                                    "Vous ne pouvez pas planifier un rendez-vous dans le passé.\n"
                                    "Veuillez choisir une date et une heure futures.")
                return
            
        # 3. Récupération des données pour l'API
        rdv_data = {
            'patient': self.patient_data.get('id'),
            'date_heure': self.datetime_input.dateTime().toString(Qt.DateFormat.ISODate),
            'motif': motif, # 🚨 La variable 'motif' est maintenant définie
            'statut': self.statut_input.currentData(), 
            'notes_internes': self.notes_input.toPlainText().strip() or None,
        }

        # 4. Appel API : Crée ou Modifie
        if self.existing_rdv_data:
            # Mode MODIFICATION
            rdv_id = self.existing_rdv_data['id']
            success, response_data = self.api_client.update_rendez_vous(rdv_id, rdv_data)
        else:
            # Mode CRÉATION
            success, response_data = self.api_client.create_rendez_vous(rdv_data)

        if success:
            # Le message de succès est géré par la fenêtre appelante (ActionDialog ou RendezVousHistoryWidget)
            self.accept()
        else:
            # Gestion des erreurs
            error_message = response_data.get('error', 'Erreur inconnue')
            QMessageBox.critical(self, "Erreur API", f"Échec de l'opération. Détails: {error_message}")


class RendezVousHistoryWidget(QWidget):
    """Affiche la liste des Rendez-vous pour un patient."""
    def __init__(self, api_client, patient_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        self.patient_data = patient_data 
        
        self.patient_id = patient_data.get('id')
        
        self.rdv_data = []
        self.init_ui()
        self.load_history()

    @staticmethod
    def _get_statut_display(statut_code):
        """Traduit le code statut de la BDD en texte lisible et couleur."""
        statut_map = {
            'P': ('Planifié', QColor("#2196F3")),    # Bleu
            'C': ('Confirmé', QColor("#4CAF50")),   # Vert
            'A': ('Annulé', QColor("#F44336")),      # Rouge
            'T': ('Terminé', QColor("#607D8B")),     # Gris
        }
        # Retourne la couleur et le nom
        name, color = statut_map.get(statut_code, ('N/A', QColor("#333333"))) 
        return color, name
    
    def init_ui(self):
        layout = QVBoxLayout(self) # 🚨 Le layout principal
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. En-tête avec bouton "Ajouter"
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Historique des Rendez-vous")) # 🚨 Ce label est visible
        header_layout.addStretch(1)
        
        self.add_button = QPushButton("📅 Planifier un RDV")
        # ... (style du bouton) ...
        self.add_button.clicked.connect(self.open_add_rendez_vous_dialog)
        header_layout.addWidget(self.add_button)
        
        layout.addLayout(header_layout)

        # 🚨 NOUVEAU : Layout pour les actions sur l'élément sélectionné 🚨
        action_row_layout = QHBoxLayout()
        
        # Bouton Modifier
        self.edit_button = QPushButton("✏️ Modifier")
        self.edit_button.clicked.connect(self.edit_selected_rdv)
        action_row_layout.addWidget(self.edit_button)
        
        # Bouton Annuler
        self.cancel_button = QPushButton("❌ Annuler")
        self.cancel_button.clicked.connect(lambda: self.update_selected_rdv_statut('A'))
        action_row_layout.addWidget(self.cancel_button)
        
        # Bouton Terminer/Compléter
        self.complete_button = QPushButton("✅ Terminer")
        self.complete_button.clicked.connect(lambda: self.update_selected_rdv_statut('T'))
        action_row_layout.addWidget(self.complete_button)
        
        action_row_layout.addStretch(1) # Pousser les boutons à gauche
        
        layout.addLayout(action_row_layout)

        # 2. Création et Configuration du Tableau
        self.table = QTableWidget()
        
      
        self.table.setColumnCount(5) 
        self.table.setHorizontalHeaderLabels(["ID", "Date et Heure", "Motif", "Notes internes", "Statut"])
        
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) 
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        
        # Connexion pour ouvrir les détails
        self.table.doubleClicked.connect(self.open_rdv_detail)
        
        # Ajustement des largeurs de colonnes
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        #Actions des boutons
        self.table.selectionModel().selectionChanged.connect(self._update_action_buttons)
        # Double-clic ouvre l'édition
        self.table.doubleClicked.connect(self.edit_selected_rdv) 

        layout.addWidget(self.table)
        self.table.hideColumn(0) 

        # Initialiser l'état des boutons (désactivés par défaut)
        self._update_action_buttons()

        layout.addWidget(self.table) 
        
        self.table.hideColumn(0) # Masquer l'ID
        self.table.doubleClicked.connect(self.edit_selected_rdv)
    
    def load_history(self):
        """Charge l'historique des rendez-vous depuis l'API pour ce patient."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # 🚨 Appel API (doit filtrer par patient_id)
        response_data = self.api_client.get_rendez_vous(patient_id=self.patient_id) 
        QApplication.restoreOverrideCursor()

        if isinstance(response_data, list):
            # 🚨 Stockage CORRECT des données de l'historique des RDV
            self.rdv_data = sorted(response_data, key=lambda x: x.get('date_heure', ''), reverse=True)
            self.update_table() # Doit appeler la mise à jour du tableau
        else:
            # S'il y a une erreur API, affiche un message mais self.rdv_data reste vide
            error_msg = response_data.get('error', "Impossible de charger l'historique des rendez-vous. Vérifiez le back-end.")
            QMessageBox.critical(self.parent(), "Erreur API", error_msg)
            self.rdv_data = [] # Assure que la liste est vide en cas d'erreur


    def open_add_rendez_vous_dialog(self):
        """Ouvre la boîte de dialogue pour ajouter un nouveau rendez-vous."""
        # 🚨 Assurez-vous que AddRendezVousDialog est accessible via un import
        dialog = AddRendezVousDialog(
            api_client=self.api_client, 
            patient_data=self.patient_data, 
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Recharger l'historique après un ajout réussi
            self.load_history()


    def get_statut_display(self, statut_code):
        """Traduit le code statut de la BDD en texte lisible."""
        # Basé sur le modèle Suivi et RendezVous
        statut_map = {
            'P': ('Planifié', QColor("#2196F3")),    # Bleu
            'C': ('Confirmé', QColor("#4CAF50")),   # Vert
            'A': ('Annulé', QColor("#F44336")),      # Rouge
            'T': ('Terminé', QColor("#607D8B")),     # Gris
        }
        return statut_map.get(statut_code, ('N/A', QColor("#333333")))


    def update_table(self):
        """Met à jour le tableau avec les données de l'historique des rendez-vous."""
        
        # 🚨 ÉTAPE CRUCIALE 1 : Vider le tableau
        self.table.setRowCount(0) 
        
        # 🚨 ÉTAPE CRUCIALE 2 : Utiliser self.rdv_data (et non self.follow_ups_data)
        self.table.setRowCount(len(self.rdv_data))
        
        for row, rdv in enumerate(self.rdv_data):
            
            # 1. ID
            item_id = QTableWidgetItem(str(rdv.get('id', 'N/A')))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, item_id)
            
            # 2. Date et Heure
            date_heure_str = rdv.get('date_heure', 'N/A')
            try:
                # Utilisation de datetime.fromisoformat est plus robuste ici
                dt = datetime.fromisoformat(date_heure_str)
                date_display = dt.strftime("%d/%m/%Y à %H:%M")
            except ValueError:
                date_display = date_heure_str
                
            self.table.setItem(row, 1, QTableWidgetItem(date_display))
            
            # 3. Motif
            self.table.setItem(row, 2, QTableWidgetItem(rdv.get('motif', 'N/A')))
            
            #4. Notes internes
            notes = rdv.get('notes_internes', '—') # Afficher '—' si vide
            item_notes = QTableWidgetItem(notes)
            self.table.setItem(row, 3, item_notes)

            # 5. Statut
            statut_code = rdv.get('statut')
            statut_color, statut_text = self._get_statut_display(statut_code)
            
            item_statut = QTableWidgetItem(statut_text)
            item_statut.setForeground(statut_color)
            item_statut.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, item_statut)

            
        self.table.hideColumn(0) # Optionnel: masquer l'ID

    def open_rdv_detail(self):
        """Redirige simplement vers l'édition suite au double-clic sur le tableau."""
        # Dans ce contexte, on suppose que le double-clic doit ouvrir l'édition
        self.edit_selected_rdv()
    
    def _get_selected_rdv_data(self):
        """Récupère les données complètes du RDV sélectionné."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            if selected_row < len(self.rdv_data):
                return self.rdv_data[selected_row]
        return None

    def _update_action_buttons(self):
        """Active/désactive les boutons d'action basés sur la sélection et le statut."""
        rdv = self._get_selected_rdv_data()
        
        # Actions permises si le RDV est sélectionné ET Planifié (P) ou Confirmé (C)
        can_act = rdv is not None and rdv.get('statut') in ['P', 'C'] 
        is_terminated = rdv is not None and rdv.get('statut') == 'T'
        is_cancelled = rdv is not None and rdv.get('statut') == 'A'
        
        self.edit_button.setEnabled(can_act)
        self.cancel_button.setEnabled(can_act)
        self.complete_button.setEnabled(can_act)

        if is_terminated:
            self.complete_button.setText("Terminé (Déjà)")
            self.edit_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif is_cancelled:
            self.complete_button.setText("Annulé (Déjà)")
            self.edit_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        else:
            self.complete_button.setText("✅ Terminer")
    
    # 🚨 LA MÉTHODE MANQUANTE 🚨
    def edit_selected_rdv(self):
        """Ouvre le dialogue pour modifier le RDV sélectionné."""
        rdv_data = self._get_selected_rdv_data()
        if not rdv_data or rdv_data.get('statut') in ['A', 'T']:
            # Empêcher l'édition si non sélectionné ou si terminé/annulé
            QMessageBox.warning(self, "Action Impossible", "Sélectionnez un rendez-vous Planifié ou Confirmé pour l'éditer.")
            return

        # Réutilisation du dialogue AddRendezVousDialog en mode édition
        edit_dialog = AddRendezVousDialog(
            api_client=self.api_client, 
            patient_data={'id': self.patient_id}, 
            existing_rdv_data=rdv_data, 
            parent=self
        )
        
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Succès", "Rendez-vous modifié avec succès.")
            self.load_history() # Recharger l'historique

    def update_selected_rdv_statut(self, new_statut_code):
        """Met à jour le statut du RDV sélectionné (Annulé ou Terminé)."""
        rdv_data = self._get_selected_rdv_data()
        if not rdv_data or rdv_data.get('statut') not in ['P', 'C']:
            return

        statut_text = "Annuler" if new_statut_code == 'A' else "Compléter"
        
        reply = QMessageBox.question(self, f"Confirmer {statut_text}",
            f"Voulez-vous vraiment **{statut_text.lower()}** le rendez-vous du {rdv_data['date_heure'][:10]} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            update_data = {'statut': new_statut_code}
            success, response_data = self.api_client.update_rendez_vous(rdv_data['id'], update_data)
            
            if success:
                QMessageBox.information(self, "Succès", f"Rendez-vous {statut_text.lower()} avec succès.")
                self.load_history() # Recharger pour mettre à jour la table et les boutons
            else:
                error_message = response_data.get('error', 'Erreur inconnue')
                QMessageBox.critical(self, "Erreur API", f"Échec de la mise à jour : {error_message}")

# ---------------------------------------------------------------------
# 3. Fenêtre Principale du Dossier Patient
# ---------------------------------------------------------------------

class PatientFolderWindow(QMainWindow):
    """
    Fenêtre dédiée pour afficher l'historique complet (suivis et RDV) d'un patient.
    """
    def __init__(self, api_client: ApiClient, patient_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data
        
        patient_name = f"{patient_data.get('last_name', '')} {patient_data.get('first_name', '')}"
        self.setWindowTitle(f"Dossier Patient : {patient_name}")
        self.setMinimumSize(900, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: white;")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        

        # 1. En-tête du Dossier Patient
        header_widget = self._create_patient_header()
        main_layout.addWidget(header_widget)
        
        # Ligne de séparation
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: #DDD;")
        main_layout.addWidget(separator)

        # 2. Zone des Onglets (Historique)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #DDD; }
            QTabBar::tab { padding: 10px 15px; background: #EEE; }
            QTabBar::tab:selected { background: white; border-top: 2px solid #2E7D32; }
        """)

        # Ajout des widgets d'historique
        self.follow_up_history = FollowUpHistoryWidget(
            api_client=self.api_client, 
            patient_id=self.patient_data.get('id')
        )
        self.rdv_history = RendezVousHistoryWidget(
            api_client=self.api_client, 
            patient_data=self.patient_data,
            parent=self.tab_widget
        )
        self.tab_widget.addTab(self.rdv_history, "🗓️ Rendez-vous")
        self.tab_widget.addTab(self.follow_up_history, "Historique des Suivis (Dossier Médical)")
        self.tab_widget.addTab(self.rdv_history, "Historique des Rendez-vous")
        
        main_layout.addWidget(self.tab_widget)

    def _create_patient_header(self):
        """Crée l'en-tête affichant les informations de base du patient."""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Nom et ID
        full_name = f"{self.patient_data.get('last_name', 'N/A').upper()} {self.patient_data.get('first_name', 'N/A')}"
        id_label = QLabel(f"Dossier n°{self.patient_data.get('id', 'N/A')}")
        id_label.setStyleSheet(f"font-size: 12pt; color: {COLOR_FOLDER_GRAY};")

        name_label = QLabel(full_name)
        name_label.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {COLOR_PRIMARY};")

        header_layout.addWidget(id_label)
        header_layout.addWidget(name_label)
        
        # Détails secondaires
        details_layout = QHBoxLayout()
        details_layout.setSpacing(25)
        
        # Liste des détails à afficher
        details = [
            ("Login", self.patient_data.get('username')),
            ("Tél.", self.patient_data.get('telephone')),
            ("Urgence",self.patient_data.get('numero_urgence')),
            ("Email", self.patient_data.get('email')),
            ("Gr. Sang.", self.patient_data.get('groupe_sanguin')),
            ("Adresse", self.patient_data.get('adresse')),
        ]
        
        for label, value in details:
            if value:
                details_layout.addWidget(QLabel(f"<b>{label}:</b> {value}"))
        
        details_layout.addStretch(1)
        header_layout.addLayout(details_layout)
        
        return header_widget

    def _get_selected_rdv_data(self):
        """Récupère les données complètes du RDV sélectionné."""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            if selected_row < len(self.rdv_data):
                return self.rdv_data[selected_row]
        return None

    def _update_action_buttons(self):
        """Active/désactive les boutons d'action basés sur la sélection et le statut."""
        rdv = self._get_selected_rdv_data()
        
        # Actions permises si le RDV est sélectionné ET Planifié (P) ou Confirmé (C)
        can_act = rdv is not None and rdv.get('statut') in ['P', 'C'] 
        is_terminated = rdv is not None and rdv.get('statut') == 'T'
        is_cancelled = rdv is not None and rdv.get('statut') == 'A'
        
        self.edit_button.setEnabled(can_act)
        self.cancel_button.setEnabled(can_act)
        self.complete_button.setEnabled(can_act) # Le bouton Terminer est activé si can_act

        # Mise à jour du texte du bouton Terminer pour un meilleur feedback
        if is_terminated:
            self.complete_button.setText("Terminé (Déjà)")
            self.edit_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        elif is_cancelled:
            self.complete_button.setText("Annulé (Déjà)")
            self.edit_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
        else:
            self.complete_button.setText("✅ Terminer")
    
    def edit_selected_rdv(self):
        """Ouvre le dialogue pour modifier le RDV sélectionné."""
        rdv_data = self._get_selected_rdv_data()
        if not rdv_data or rdv_data.get('statut') in ['A', 'T']:
            # Empêcher l'édition si non sélectionné ou si terminé/annulé
            return

        # Réutilisation du dialogue AddRendezVousDialog en mode édition
        edit_dialog = AddRendezVousDialog(
            api_client=self.api_client, 
            patient_data={'id': self.patient_id}, 
            existing_rdv_data=rdv_data, 
            default_datetime=None,
            parent=self
        )
        
        if edit_dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Succès", "Rendez-vous modifié avec succès.")
            self.load_history() # Recharger l'historique

    def update_selected_rdv_statut(self, new_statut_code):
        """Met à jour le statut du RDV sélectionné (Annulé ou Terminé)."""
        rdv_data = self._get_selected_rdv_data()
        if not rdv_data or rdv_data.get('statut') not in ['P', 'C']:
            return

        statut_text = "Annuler" if new_statut_code == 'A' else "Compléter"
        
        reply = QMessageBox.question(self, f"Confirmer {statut_text}",
            f"Voulez-vous vraiment **{statut_text.lower()}** le rendez-vous du {rdv_data['date_heure'][:10]} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            update_data = {'statut': new_statut_code}
            success, response_data = self.api_client.update_rendez_vous(rdv_data['id'], update_data)
            
            if success:
                QMessageBox.information(self, "Succès", f"Rendez-vous {statut_text.lower()} avec succès.")
                self.load_history() # Recharger pour mettre à jour la table et les boutons
            else:
                error_message = response_data.get('error', 'Erreur inconnue')
                QMessageBox.critical(self, "Erreur API", f"Échec de la mise à jour : {error_message}")
    
    