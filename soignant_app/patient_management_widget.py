# desktop_app/patient_management_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableView, QHeaderView, QMessageBox, QDialog, QApplication,
    QTabWidget, QFormLayout, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from .utils.api_client import ApiClient
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QDateTime
# Import du formulaire d'ajout/modification de patient
from .add_patient_dialog import AddPatientDialog 

# --- Définition des Couleurs Clés ---
COLOR_MAIN_GREEN = "#4CAF50"
COLOR_DARK_GREEN = "#388E3C"
COLOR_MAIN_WHITE = "#FFFFFF"
COLOR_MAIN_TEXT = "#333333"
COLOR_BORDER_GREY = "#CCCCCC"
COLOR_DANGER_RED = "#D32F2F" 

class PatientTableModel(QAbstractTableModel):
    """
    Modèle de données personnalisé pour l'affichage des patients dans QTableView, 
    assurant la correspondance avec les champs de l'API Django.
    """
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self.headers = [
            "ID", "Numéro Patient", "Nom", "Prénom", 
            "Téléphone", "Urgence", 
            "Email", "Date de Naissance", "Groupe Sanguin"
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        patient = self._data[index.row()]
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return patient.get('id')
            if col == 1: return patient.get('numero_patient')
            if col == 2: return patient.get('last_name')
            if col == 3: return patient.get('first_name')
            if col == 4: return patient.get('telephone')      
            if col == 5: return patient.get('numero_urgence')  
            if col == 6: return patient.get('email')
            if col == 7: return patient.get('date_naissance')
            if col == 8: return patient.get('groupe_sanguin')
            
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 0: return Qt.AlignmentFlag.AlignCenter 
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
            
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return QVariant()

    def setPatientsData(self, data):
        """Met à jour les données du modèle."""
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def getPatient(self, row):
        """Retourne l'objet patient pour une ligne donnée."""
        if 0 <= row < len(self._data):
            return self._data[row]
        return None


#### Début Classe PatientDetails
class PatientDetailDialog(QDialog):
    """
    Fenêtre de dialogue affichant l'ensemble des informations de suivi du patient
    (Infos, Contact Urgence, Relevés, Suivis, RDV, etc.)
    """
    def __init__(self, api_client, patient_id, patient_full_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Carnet Médical - {patient_full_data.get('first_name')} {patient_full_data.get('last_name')}")
        self.setMinimumSize(900, 700)
        self.api_client = api_client
        self.patient_id = patient_id
        self.patient_data = patient_full_data 
        
        self.main_layout = QVBoxLayout(self)
        
        self._setup_ui()
        self.load_all_data()

    def _setup_ui(self):
        # 1. En-tête
        header_layout = QHBoxLayout()
        name_label = QLabel(f"<h2>{self.patient_data.get('first_name')} {self.patient_data.get('last_name')}</h2>")
        id_label = QLabel(f"**N° Patient :** {self.patient_data.get('numero_patient')}")
        header_layout.addWidget(name_label)
        header_layout.addStretch(1)
        header_layout.addWidget(id_label)
        self.main_layout.addLayout(header_layout)

        # 2. Onglets de Détail
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_info_and_urgence_tab(), "Infos Générales & Urgence")
        self.tabs.addTab(self._create_medical_record_tab(), "Dossier Médical")
        self.tabs.addTab(self._create_suivis_rdv_tab(), "Suivis Cliniques & RDV")
        self.tabs.addTab(self._create_vitals_tab(), "Relevés Vitaux")
        self.main_layout.addWidget(self.tabs)
        
        # 3. Bouton de Fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        self.main_layout.addWidget(close_button)

    # --- Création des Onglets ---
    
    def _create_info_and_urgence_tab(self):
        """ Onglet Informations Personnelles et Contact d'Urgence (Lecture seule). """
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Groupe 1: Infos de Base (champs du modèle Patient)
        base_group = QGroupBox("Informations d'Identification (Modèle Patient)")
        base_form = QFormLayout(base_group)
        
        # Remplissage des champs (Lecture seule)
        fields = [
            ("Username:", self.patient_data.get('username', 'N/A')),
            ("Email:", self.patient_data.get('email', 'N/A')),
            ("Téléphone:", self.patient_data.get('telephone', 'N/A')),
            ("Urgence (Tél.):", self.patient_data.get('numero_urgence', 'N/A')),
        ]
        for label, value in fields:
            input_field = QLineEdit(str(value))
            input_field.setReadOnly(True)
            base_form.addRow(label, input_field)
            
        layout.addRow(base_group)
        
        # Groupe 2: Contact d'Urgence (champs supplémentaires)
        urgence_group = QGroupBox("Contact d'Urgence (Modèle Patient)")
        urgence_form = QFormLayout(urgence_group)
        
        # Remplissage des champs (Contact Urgence)
        urgence_fields = [
            ("Nom Contact:", self.patient_data.get('contact_urgence_nom', 'N/A')), # Nouveau champ
            ("Lien de Parenté:", self.patient_data.get('contact_urgence_lien', 'N/A')), # Nouveau champ
            ("Téléphone Contact:", self.patient_data.get('contact_urgence_telephone', 'N/A')), # Nouveau champ
        ]
        for label, value in urgence_fields:
            input_field = QLineEdit(str(value))
            input_field.setReadOnly(True)
            urgence_form.addRow(label, input_field)
            
        layout.addRow(urgence_group)
        layout.addRow(QLabel("Note: Utilisez le bouton 'Modifier' dans la liste pour changer ces informations."))
        
        return widget

    def _create_medical_record_tab(self):
        """ Onglet Dossier Médical et informations du plan de suivi. """
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Groupe 1: Infos Médicales Clés
        medical_group = QGroupBox("Statut Médical Clé")
        medical_form = QFormLayout(medical_group)
        
        medical_fields = [
            ("Date de Naissance:", self.patient_data.get('date_naissance', 'N/A')), 
            ("Groupe Sanguin:", self.patient_data.get('groupe_sanguin', 'N/A')), 
            ("Poids (kg):", self.patient_data.get('poids_kg', 'N/A')), # Champ du modèle Patient
            ("Taille (cm):", self.patient_data.get('taille_cm', 'N/A')), # Champ du modèle Patient
        ]
        for label, value in medical_fields:
            input_field = QLineEdit(str(value))
            input_field.setReadOnly(True)
            medical_form.addRow(label, input_field)
            
        layout.addRow(medical_group)
        
        # Groupe 2: Plan de Suivi/Seuils (Placeholder)
        plan_group = QGroupBox("Plan de Suivi et Seuils Critiques")
        plan_form = QFormLayout(plan_group)
        plan_form.addRow(QLabel("Tension Max (Alerte):"), QLineEdit("160/100")) # Placeholder
        plan_form.addRow(QLabel("Glycémie Cible:"), QLineEdit("1.0 g/L")) # Placeholder
        plan_form.addRow(QLabel(""), QLabel("À implémenter : Chargement des détails du plan de suivi."))
        
        layout.addRow(plan_group)
        
        return widget

    def _create_suivis_rdv_tab(self):
        """ Onglet Historique des Suivis Cliniques et Rendez-vous. """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Historique des Suivis
        suivis_group = QGroupBox("Historique des Suivis Cliniques")
        suivis_layout = QVBoxLayout(suivis_group)
        self.suivis_table = QTableWidget()
        self.suivis_table.setColumnCount(4)
        self.suivis_table.setHorizontalHeaderLabels(["Date", "Motif", "Notes", "Prescriptions"])
        self.suivis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        suivis_layout.addWidget(self.suivis_table)
        
        add_suivi_btn = QPushButton("➕ Ajouter un Nouveau Suivi Clinique")
        suivis_layout.addWidget(add_suivi_btn)
        layout.addWidget(suivis_group)
        
        # Historique des Rendez-vous
        rdv_group = QGroupBox("Historique des Rendez-vous")
        rdv_layout = QVBoxLayout(rdv_group)
        self.rdv_table = QTableWidget()
        self.rdv_table.setColumnCount(4)
        self.rdv_table.setHorizontalHeaderLabels(["Date/Heure", "Motif", "Statut", "Action"])
        self.rdv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rdv_layout.addWidget(self.rdv_table)
        
        layout.addWidget(rdv_group)
        
        return widget
        
    def _create_vitals_tab(self):
        """ Onglet Historique des Relevés Vitaux. """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Graphique (Placeholder)
        layout.addWidget(QLabel("<h2>GRAPHIQUE DES TENDANCES (Tension, Glycémie)</h2>"))
        layout.addWidget(QLabel("À implémenter: Widget de graphique interactif (ex: PyQtGraph)."))
        
        # Tableau des relevés vitaux
        vitals_group = QGroupBox("Historique des Relevés Détaillés")
        vitals_layout = QVBoxLayout(vitals_group)
        self.vitals_table = QTableWidget()
        self.vitals_table.setColumnCount(4)
        self.vitals_table.setHorizontalHeaderLabels(["Date/Heure", "Tension (Sys/Dia)", "Glycémie", "Poids"])
        self.vitals_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        vitals_layout.addWidget(self.vitals_table)
        
        layout.addWidget(vitals_group)
        
        return widget
        
    # --- Chargement des Données (Fonctions d'appel API) ---

    def load_all_data(self):
        """ Lance le chargement des données des suivis, RDV, etc. """
        # Ces méthodes doivent être implémentées en utilisant self.api_client
        self._load_suivis_data()
        self._load_rdv_data()
        self._load_vitals_data()

    def _load_suivis_data(self):
        # Placeholder pour l'appel API:
        # data = self.api_client.get_suivis(self.patient_id)
        
        # Simulation de données
        suivis = [
            {'date_suivi': '2025-01-15T10:30:00Z', 'motif': 'Bilan de routine', 'notes_medecin': 'Patient stable.', 'prescriptions': 'Rien'},
            {'date_suivi': '2025-01-01T14:00:00Z', 'motif': 'Crise hypertensive', 'notes_medecin': 'Ajustement du dosage.', 'prescriptions': 'Lisinopril 5mg'},
        ]
        
        self.suivis_table.setRowCount(len(suivis))
        for row, s in enumerate(suivis):
            self.suivis_table.setItem(row, 0, QTableWidgetItem(s['date_suivi'][:10]))
            self.suivis_table.setItem(row, 1, QTableWidgetItem(s['motif']))
            self.suivis_table.setItem(row, 2, QTableWidgetItem(s['notes_medecin']))
            self.suivis_table.setItem(row, 3, QTableWidgetItem(s['prescriptions']))

    def _load_rdv_data(self):
        # Placeholder pour l'appel API:
        # data = self.api_client.get_rdv(self.patient_id)

        # Simulation de données
        rdv_list = [
            {'date_heure': '2025-03-01T11:00:00Z', 'motif': 'Contrôle post-ajustement', 'statut': 'Planifié'},
            {'date_heure': '2025-01-01T14:00:00Z', 'motif': 'Urgence', 'statut': 'Terminé'},
        ]
        
        self.rdv_table.setRowCount(len(rdv_list))
        for row, rdv in enumerate(rdv_list):
            self.rdv_table.setItem(row, 0, QTableWidgetItem(rdv['date_heure'][:16]))
            self.rdv_table.setItem(row, 1, QTableWidgetItem(rdv['motif']))
            self.rdv_table.setItem(row, 2, QTableWidgetItem(rdv['statut']))
            
            action_btn = QPushButton("Gérer")
            # 🚨 Connexion à une fonction de gestion du statut
            # action_btn.clicked.connect(lambda _, r=rdv: self.update_rdv_status(r['id']))
            self.rdv_table.setCellWidget(row, 3, action_btn)

    def _load_vitals_data(self):
        # Placeholder pour l'appel API
        # self.vitals_table.setRowCount(...)
        pass
        
# --- FIN DE LA CLASSE PatientDetailDialog ---

class PatientManagementWidget(QWidget):
    """
    Widget principal pour l'affichage, la recherche et la gestion des patients.
    """
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.init_ui()
        self.load_patients() 

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        button_style_base = f"""
            QPushButton {{
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
                font-weight: bold;
            }}
        """

        # 1. Zone de Recherche et Bouton Ajouter (en haut)
        search_container = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, prénom, email ou ID...")
        self.search_input.setStyleSheet(f"QLineEdit {{ border: 1px solid {COLOR_BORDER_GREY}; border-radius: 4px; padding: 8px; }}")
        
        search_button = QPushButton("🔍 Rechercher")
        search_button.setStyleSheet(button_style_base + f"QPushButton {{ background-color: {COLOR_MAIN_GREEN}; color: {COLOR_MAIN_WHITE}; }} QPushButton:hover {{ background-color: {COLOR_DARK_GREEN}; }}")

        add_button = QPushButton("➕ Ajouter Patient")
        add_button.setStyleSheet(button_style_base + f"QPushButton {{ background-color: {COLOR_MAIN_GREEN}; color: {COLOR_MAIN_WHITE}; }} QPushButton:hover {{ background-color: {COLOR_DARK_GREEN}; }}")

        search_container.addWidget(self.search_input)
        search_container.addWidget(search_button)
        search_container.addWidget(add_button)

        main_layout.addLayout(search_container)

        # 2. Tableau d'Affichage des Patients
        self.table_view = QTableView()
        self.patient_model = PatientTableModel()
        self.table_view.setModel(self.patient_model)
        
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)

        main_layout.addWidget(self.table_view)
        
        # 3. Boutons d'Action (Modifier et Supprimer)
        action_container = QHBoxLayout()
        action_container.addStretch(1) # Pousse les boutons à droite

        self.edit_button = QPushButton("✏️ Modifier")
        self.edit_button.setStyleSheet(button_style_base + f"QPushButton {{ background-color: #FFC107; color: {COLOR_MAIN_TEXT}; }} QPushButton:hover {{ background-color: #FFB300; }}")

        self.delete_button = QPushButton("🗑️ Supprimer")
        self.delete_button.setStyleSheet(button_style_base + f"QPushButton {{ background-color: {COLOR_DANGER_RED}; color: {COLOR_MAIN_WHITE}; }} QPushButton:hover {{ background-color: #C62828; }}")

        action_container.addWidget(self.edit_button)
        action_container.addWidget(self.delete_button)
        
        main_layout.addLayout(action_container)

        #3- Bouton de détails
        detail_view_container = QHBoxLayout()
        self.detail_view_button = QPushButton("👁️ Voir Détails/Carnet Médical (Suivi)")
        self.detail_view_button.setStyleSheet(button_style_base + f"QPushButton {{ background-color: #1976D2; color: {COLOR_MAIN_WHITE}; }} QPushButton:hover {{ background-color: #1565C0; }}")
        
        detail_view_container.addWidget(QLabel("Action pour le patient sélectionné:"))
        detail_view_container.addWidget(self.detail_view_button)
        detail_view_container.addStretch(1) 
        
        main_layout.addLayout(detail_view_container)

        # Connexions
        search_button.clicked.connect(self.load_patients)
        self.search_input.returnPressed.connect(self.load_patients)
        add_button.clicked.connect(self.open_add_patient_dialog)
        self.table_view.doubleClicked.connect(self.open_patient_detail)
        
        self.detail_view_button.clicked.connect(self.open_patient_detail_dialog) # Bouton Détails
        self.table_view.doubleClicked.connect(self.open_patient_detail_dialog_from_index) # Double-clic

        # Connexion des boutons Modifier et Supprimer
        self.edit_button.clicked.connect(self.open_edit_patient_dialog)
        self.delete_button.clicked.connect(self.delete_patient)


    def get_selected_patient(self):
        """Récupère l'objet patient sélectionné dans le tableau."""
        selected_rows = self.table_view.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Sélection Requise", "Veuillez sélectionner un patient dans la liste.")
            return None
        
        row = selected_rows[0].row()
        return self.patient_model.getPatient(row)


    def load_patients(self):
        """Appelle l'API pour récupérer les patients avec le terme de recherche."""
        search_term = self.search_input.text().strip()
        
        self.search_input.setDisabled(True)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        data = self.api_client.get_patients(search_term)
        
        QApplication.restoreOverrideCursor()
        self.search_input.setDisabled(False)
        
        if isinstance(data, dict) and 'error' in data:
            QMessageBox.critical(self, "Erreur API", data['error'])
            self.patient_model.setPatientsData([])
            return
        
        self.patient_model.setPatientsData(data)


    def open_add_patient_dialog(self):
        """Ouvre la boîte de dialogue d'ajout de patient."""
        dialog = AddPatientDialog(api_client=self.api_client, parent=self) 
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
             self.load_patients() 
        else:
             pass


    def open_edit_patient_dialog(self):
        """Ouvre la boîte de dialogue pour modifier les informations du patient sélectionné."""
        patient_to_edit = self.get_selected_patient()
        if not patient_to_edit:
            return
            
        # Utilisation de AddPatientDialog en mode édition (en passant les données du patient)
        dialog = AddPatientDialog(api_client=self.api_client, patient_data=patient_to_edit, parent=self) 
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
             self.load_patients() 
        else:
             pass


    def delete_patient(self):
        """Supprime le patient sélectionné après confirmation."""
        patient_to_delete = self.get_selected_patient()
        if not patient_to_delete:
            return

        reply = QMessageBox.question(self, "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer définitivement le patient : **{patient_to_delete.get('first_name')} {patient_to_delete.get('last_name')}** (ID: {patient_to_delete.get('numero_patient')}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            patient_id = patient_to_delete['id'] # L'ID principal (pk) du patient
            
            # Appel de la méthode DELETE
            result = self.api_client.delete_patient(patient_id)
            
            if result is True:
                QMessageBox.information(self, "Succès", f"Le patient {patient_to_delete.get('last_name')} a été supprimé.")
                self.load_patients()
            else:
                QMessageBox.critical(self, "Erreur de Suppression", 
                                     f"Échec de la suppression.\nDétails: {result.get('error')}")


    def open_patient_detail_dialog_from_index(self, index):
        """Ouvre les détails suite à un double-clic sur le tableau."""
        patient = self.patient_model.getPatient(index.row())
        if patient:
            self.open_patient_detail_dialog(patient_data=patient)


    def open_patient_detail_dialog(self, patient_data=None):
        """Ouvre la modale/fenêtre de détail et de suivi du patient."""
        if patient_data is None:
            patient_data = self.get_selected_patient()
        
        if not patient_data:
            return

        # Ouvrir la fenêtre modale de détail
        dialog = PatientDetailDialog(
            api_client=self.api_client, 
            patient_id=patient_data['id'], 
            patient_full_data=patient_data, 
            parent=self
        )
        dialog.exec()