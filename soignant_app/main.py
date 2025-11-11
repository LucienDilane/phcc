# desktop_app/main_window.py (Mise à Jour de la Recherche)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QMenu, QDialog, QApplication,
    QStackedWidget, QListWidget, QListWidgetItem, QFrame,
    QAbstractScrollArea,QAbstractScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont
# Assurez-vous que ces fichiers existent dans desktop_app/utils/ et desktop_app/
from .utils.api_client import ApiClient
from .dashboard_widget import DashboardWidget 
from .agenda_widget import AgendaAndPlansWidget
from .add_patient_dialog import AddPatientDialog 
from .add_follow_up_dialog import AddFollowUpDialog 
from .patient_folder_window import PatientFolderWindow 
from .stats_widget import StatsWidget
import logging
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- Définition des Couleurs Clés ---
COLOR_PRIMARY = "#2E7D32"       
COLOR_ACCENT = "#4CAF50"        
COLOR_BACKGROUND = "#F5F5F5"    
COLOR_TEXT_DARK = "#333333"     
COLOR_DANGER_RED = "#C62828"     
COLOR_WARNING_YELLOW = "#FFC107"  
COLOR_FOLLOW_UP_BLUE = "#1976D2"  
COLOR_FOLDER_GRAY = "#607D8B"     
COLOR_NAVBAR_BG = "#1B5E20"      
COLOR_NAVBAR_TEXT = "#E8F5E9"    

# ---------------------------------------------------------------------
# VUES DÉDIÉES (Contenu des pages du QStackedWidget)
# ---------------------------------------------------------------------

class PatientsView(QWidget):
    """
    Vue dédiée à la liste et gestion des patients. 
    Maintenant avec un bouton de recherche explicite.
    """
    def __init__(self, main_window, api_client: ApiClient):
        super().__init__()
        self.main_window = main_window
        self.api_client = api_client
        self.patients_data = [] 
        self.init_ui()
        self.load_patients_data() # Charge les données initiales

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Gestion des Patients")
        title_label.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {COLOR_PRIMARY}; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # 1. Barre de Recherche et Boutons d'Action 
        action_layout = QHBoxLayout()
        
        # Champ de Recherche
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un patient (Nom, Prénom, Login, Téléphone)...")
        self.search_input.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 5px; font-size: 11pt;")
        self.search_input.returnPressed.connect(self.load_patients_data) # 🚨 Recherche sur la touche Entrée

        # Bouton Chercher (NOUVEAU)
        self.search_button = QPushButton("🔍 Chercher")
        self.search_button.setStyleSheet(f"QPushButton {{ background-color: {COLOR_ACCENT}; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold; }}")
        self.search_button.clicked.connect(self.load_patients_data) # 🚨 Connecté à la fonction de recherche
        
        # Bouton Rafraîchir
        self.refresh_button = QPushButton("🔄 Rafraîchir")
        self.refresh_button.setStyleSheet(f"QPushButton {{ background-color: #E0E0E0; color: {COLOR_TEXT_DARK}; padding: 10px 15px; border-radius: 5px; font-weight: bold; }}")
        self.refresh_button.clicked.connect(self.load_patients_data)
        
        # Boutons d'Action sur la sélection
        self.edit_button = QPushButton("✏️ Modifier Patient")
        self.edit_button.setStyleSheet(f"QPushButton {{ background-color: {COLOR_WARNING_YELLOW}; color: {COLOR_TEXT_DARK}; padding: 10px 15px; border-radius: 5px; font-weight: bold; }}")
        self.edit_button.clicked.connect(self.main_window.open_edit_selected_patient)
        self.edit_button.setEnabled(False) 

        self.delete_button = QPushButton("🗑️ Supprimer Patient")
        self.delete_button.setStyleSheet(f"QPushButton {{ background-color: {COLOR_DANGER_RED}; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold; }}")
        self.delete_button.clicked.connect(self.main_window.confirm_delete_selected_patient)
        self.delete_button.setEnabled(False) 
        
        self.add_patient_button = QPushButton("➕ Ajouter Patient")
        self.add_patient_button.setStyleSheet(f"""
            QPushButton {{ background-color: {COLOR_ACCENT}; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {COLOR_PRIMARY}; }}
        """)
        self.add_patient_button.clicked.connect(self.main_window.open_add_patient_dialog)
        
        # Mise en page des actions
        search_group_layout = QHBoxLayout()
        search_group_layout.addWidget(self.search_input)
        search_group_layout.addWidget(self.search_button) # Ajout du bouton Chercher

        action_layout.addLayout(search_group_layout)
        action_layout.addWidget(self.refresh_button)
        action_layout.addStretch(1)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.add_patient_button)
        main_layout.addLayout(action_layout)
        
        # 🚨 Suppression du QTimer de recherche (Plus nécessaire avec le bouton)
        # self.search_timer.timeout.connect(self.load_patients_data)
        # self.search_input.textChanged.connect(self.search_timer.start)


        # 2. Tableau des Patients (inchangé)
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(10) 
        self.patient_table.setHorizontalHeaderLabels([
            "ID", "Login", "Nom", "Prénom", "Groupe Sang.", "Téléphone", 
            "Num. Urgence", "Email", "Adresse", "Actions" 
        ])
        
        self.patient_table.setStyleSheet("""
            QTableWidget { border: 1px solid #DDD; gridline-color: #EEE; }
            QHeaderView::section { background-color: #E0E0E0; padding: 5px; border: 1px solid #DDD; font-weight: bold; }
        """)
        
        header = self.patient_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents) 

        self.patient_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.patient_table.customContextMenuRequested.connect(self.main_window.show_context_menu)
        self.patient_table.doubleClicked.connect(self.main_window.open_patient_folder_selected) 
        self.patient_table.itemSelectionChanged.connect(self.toggle_action_buttons) 
        
        main_layout.addWidget(self.patient_table)
        
    def toggle_action_buttons(self):
        """Active/désactive les boutons Modifier et Supprimer en fonction de la sélection."""
        has_selection = bool(self.patient_table.selectedItems())
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    def load_patients_data(self):
        """Charge les données des patients depuis l'API, en utilisant le terme de recherche."""
        search_term = self.search_input.text().strip()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # L'API client doit gérer le passage du search_term en paramètre de requête.
        response_data = self.api_client.get_patients(search_term=search_term) 
        
        QApplication.restoreOverrideCursor()

        if isinstance(response_data, dict) and 'error' in response_data:
            # Affiche l'erreur via une QMessageBox
            QMessageBox.critical(self.main_window, "Erreur de Chargement", response_data['error'])
            self.patients_data = [] # 👈 Assure que la liste est vide en cas d'échec
        elif isinstance(response_data, list):
            self.patients_data = response_data
        else:
            # Cas d'une réponse inattendue non-liste/non-erreur
            QMessageBox.critical(self.main_window, "Erreur de Réponse", "Réponse API inattendue lors du chargement des patients.")
            self.patients_data = []

        self.update_patient_table()

    def update_patient_table(self):
        """Met à jour le QTableWidget avec les données actuelles."""
        self.patient_table.setRowCount(len(self.patients_data))
        
        for row, patient in enumerate(self.patients_data):
            
            # Colonnes d'information (Indices ajustés)
            item_id = QTableWidgetItem(str(patient.get('id', 'N/A'))); item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.patient_table.setItem(row, 0, item_id)
            item_username = QTableWidgetItem(patient.get('username', 'N/A')); self.patient_table.setItem(row, 1, item_username)
            item_last_name = QTableWidgetItem(patient.get('last_name', '')); self.patient_table.setItem(row, 2, item_last_name)
            item_first_name = QTableWidgetItem(patient.get('first_name', '')); self.patient_table.setItem(row, 3, item_first_name)
            item_blood = QTableWidgetItem(patient.get('groupe_sanguin', 'N/A')); item_blood.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.patient_table.setItem(row, 4, item_blood)
            item_phone = QTableWidgetItem(patient.get('telephone', '')); item_phone.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.patient_table.setItem(row, 5, item_phone)
            item_emergency = QTableWidgetItem(patient.get('numero_urgence', 'N/A')); item_emergency.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.patient_table.setItem(row, 6, item_emergency)
            item_email = QTableWidgetItem(patient.get('email', '')); self.patient_table.setItem(row, 7, item_email)
            item_address = QTableWidgetItem(patient.get('adresse', '')); self.patient_table.setItem(row, 8, item_address)

            # Colonne 9: Actions (Seulement Dossier et Suivi)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)
            
            folder_button = QPushButton("🗂️ Dossier")
            folder_button.setStyleSheet(f"background-color: {COLOR_FOLDER_GRAY}; color: white; border-radius: 4px; padding: 5px;")
            folder_button.clicked.connect(lambda _, p=patient: self.main_window.open_patient_folder_dialog(p))

            follow_up_button = QPushButton("➕ Suivi")
            follow_up_button.setStyleSheet(f"background-color: {COLOR_FOLLOW_UP_BLUE}; color: white; border-radius: 4px; padding: 5px;")
            follow_up_button.clicked.connect(lambda _, p=patient: self.main_window.open_add_follow_up_dialog(p))

            action_layout.addWidget(folder_button)
            action_layout.addWidget(follow_up_button)
            
            self.patient_table.setCellWidget(row, 9, action_widget) 
            
        self.patient_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.patient_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patient_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.toggle_action_buttons()

    def get_selected_patient_data(self):
        """Récupère les données du patient sélectionné (pour les actions externes)."""
        selected_rows = self.patient_table.selectedIndexes()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        return self.patients_data[row]

class RendezVousView(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        
        # 🚨 CORRECTION : Créer le layout principal UNE seule fois. 🚨
        main_layout = QVBoxLayout(self) 
        
        self.agenda_widget = AgendaAndPlansWidget(self.api_client)
        main_layout.addWidget(self.agenda_widget)
     

class StatistiquesView(QWidget):
    # 🚨 Accepte maintenant l'api_client pour résoudre le TypeError 🚨
    def __init__(self, api_client, parent=None): 
        super().__init__(parent)
        self.api_client = api_client
        self.init_ui()
        self.load_stats() # Charge les données au démarrage

    def init_ui(self):
        """Configure l'interface utilisateur avec des cartes de statistiques."""
        main_layout = QVBoxLayout(self)
        
        title_label = QLabel("Tableau de Bord & Statistiques Clés")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        self.grid_layout = QGridLayout()
        main_layout.addLayout(self.grid_layout)
        
        # Initialisation des cartes de stats.
        # Le _create_stat_card ajoute le Frame à la grille interne.
        self._create_stat_card("Total Patients", "...", "Total_Patients_value_label", 0, 0)
        self._create_stat_card("RDV cette semaine", "...", "RDV_cette_semaine_value_label", 0, 1)
        self._create_stat_card("Suivis (30 jours)", "...", "Suivis_(30_jours)_value_label", 0, 2)
        
        main_layout.addStretch(1) # Pousser les éléments vers le haut

    def _create_stat_card(self, title, value, object_name, row, col):
        """Méthode utilitaire pour créer une carte de statistiques."""
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 15px; margin: 5px;")
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setObjectName(object_name) # Pour mise à jour facile
        layout.addWidget(value_label)
        
        self.grid_layout.addWidget(frame, row, col)


    def load_stats(self):
        """Récupère les données de l'API et met à jour les cartes."""
        success, data = self.api_client.get_global_stats()
        
        if success:
            # Met à jour les labels de valeur en utilisant leur nom d'objet
            self.findChild(QLabel, "Total_Patients_value_label").setText(str(data.get('total_patients', 0)))
            self.findChild(QLabel, "RDV_cette_semaine_value_label").setText(str(data.get('rdv_this_week', 0)))
            self.findChild(QLabel, "Suivis_(30_jours)_value_label").setText(str(data.get('suivis_last_month', 0)))
            
        else:
            QMessageBox.critical(self, "Erreur Statistiques", f"Impossible de charger les statistiques globales.\nErreur: {data.get('error', 'API non disponible')}")

# ---------------------------------------------------------------------
# FENÊTRE PRINCIPALE (MainWindow)
# ---------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient, user_data: dict, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_data = user_data
        self.setWindowTitle(f"People Health Centre Dashboard - Dr. {user_data.get('last_name', 'Personnel')}")
        self.setMinimumSize(1200, 800)
        
        self.init_ui()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)


    def init_ui(self):
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {COLOR_BACKGROUND};") 
        self.setCentralWidget(central_widget)
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Barre de navigation latérale (Sidebar)
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(220) 
        self.sidebar_widget.setStyleSheet(f"background-color: {COLOR_NAVBAR_BG}; color: white;")
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(15, 20, 15, 10)

        logo_label = QLabel("People Health Centre")
        logo_label.setStyleSheet(f"color: {COLOR_NAVBAR_TEXT}; font-size: 16pt; font-weight: bold; margin-bottom: 30px;")
        sidebar_layout.addWidget(logo_label)

        # Liste de Navigation (Barre de défilement masquée)
        self.nav_list = QListWidget()
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) 
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)   
        self.nav_list.setStyleSheet(f"""
            QListWidget {{ 
                background-color: transparent; 
                border: none; 
                font-size: 13pt; 
            }}
            QListWidget::item {{ 
                padding: 12px 0px; 
                color: {COLOR_NAVBAR_TEXT}; 
                border-radius: 5px; 
            }}
            QListWidget::item:selected {{ 
                background-color: {COLOR_ACCENT}; 
                color: white; 
                font-weight: bold;
            }}
            QListWidget::item:hover {{ 
                background-color: {COLOR_PRIMARY};
            }}
        """)
        
        # Définition des pages avec Emojis
        self.pages = {
            "🏠 Dashboard": DashboardWidget(api_client=self.api_client, user_data=self.user_data), 
            "🗓️ Rendez-vous et Plans": RendezVousView(api_client=self.api_client),
            "🧑‍⚕️ Patients": PatientsView(main_window=self, api_client=self.api_client), 
            "📊 Statistiques": StatistiquesView(api_client=self.api_client)
        }
        for name in self.pages.keys():
            item = QListWidgetItem(name)
            self.nav_list.addItem(item)
            
        self.nav_list.setCurrentRow(0)
        self.nav_list.clicked.connect(self.change_view)
        
        sidebar_layout.addWidget(self.nav_list)
        
        # Info Utilisateur et Déconnexion (en bas de la sidebar)
        sidebar_layout.addStretch(1)
        
        user_info = f"Connecté : {self.user_data.get('username')}"
        self.user_label = QLabel(user_info)
        self.user_label.setStyleSheet(f"color: #A5D6A7; font-size: 11pt; margin-bottom: 5px;")
        
        self.logout_button = QPushButton("🚪 Déconnexion")
        self.logout_button.setStyleSheet(f"QPushButton {{ background-color: {COLOR_DANGER_RED}; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }}")
        self.logout_button.clicked.connect(self.logout)
        
        sidebar_layout.addWidget(self.user_label)
        sidebar_layout.addWidget(self.logout_button)

        main_h_layout.addWidget(self.sidebar_widget)

        # 2. Contenu Principal (QStackedWidget)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"background-color: white; padding: 0px;") 
        
        for view in self.pages.values():
            self.stacked_widget.addWidget(view)
            
        main_h_layout.addWidget(self.stacked_widget)
        
        self.patients_view = self.pages["🧑‍⚕️ Patients"]

    # -----------------------------------------------------------
    # Méthodes d'Action (Fonctionnement inchangé)
    # -----------------------------------------------------------
    
    def open_patient_folder_selected(self):
        patient_data = self.patients_view.get_selected_patient_data()
        if patient_data:
            self.open_patient_folder_dialog(patient_data)

    def open_edit_selected_patient(self):
        patient_data = self.patients_view.get_selected_patient_data()
        if patient_data:
            self.open_edit_patient_dialog(patient_data)

    def confirm_delete_selected_patient(self):
        patient_data = self.patients_view.get_selected_patient_data()
        if patient_data:
            self.confirm_delete_patient(patient_data)
    
    def change_view(self, index):
        row = self.nav_list.currentRow()
        self.stacked_widget.setCurrentIndex(row)
        
    def open_patient_folder_dialog(self, patient_data):
        self.patient_folder_window = PatientFolderWindow(
            api_client=self.api_client, 
            patient_data=patient_data, 
            parent=self
        )
        self.patient_folder_window.show()

    def open_add_follow_up_dialog(self, patient_data):
        dialog = AddFollowUpDialog(api_client=self.api_client, patient_data=patient_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "SUCCÈS", "Suivi créé.")
    
    def open_add_patient_dialog(self):
        dialog = AddPatientDialog(api_client=self.api_client, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.patients_view.load_patients_data()
            QMessageBox.information(self, "SUCCÈS", "Patient ajouté.")

    def open_edit_patient_dialog(self, patient_data):
        dialog = AddPatientDialog(api_client=self.api_client, patient_data=patient_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.patients_view.load_patients_data()
            QMessageBox.information(self, "SUCCÈS", "Patient modifié.")

    def confirm_delete_patient(self, patient_data):
        patient_name = f"{patient_data.get('first_name')} {patient_data.get('last_name')}"
        reply = QMessageBox.question(self, 'Confirmation de Suppression',
            f"Êtes-vous sûr de vouloir supprimer définitivement le patient : **{patient_name}** ({patient_data.get('username')}) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_patient(patient_data)
            
    def delete_patient(self, patient_data):
        patient_id = patient_data.get('id')
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        response = self.api_client.delete_patient(patient_id)
        QApplication.restoreOverrideCursor()

        if response is True:
            QMessageBox.information(self, "SUCCÈS", f"Le patient {patient_data.get('username')} a été supprimé avec succès.")
            self.patients_view.load_patients_data()
        elif isinstance(response, dict) and 'error' in response:
            details = response.get('details', 'Détails non disponibles.')
            QMessageBox.critical(self, "Erreur de Suppression", f"Échec de la suppression.\n\nErreur : {details}")
        else:
             QMessageBox.critical(self, "Erreur de Suppression", "Une erreur inattendue est survenue lors de la suppression.")

    def show_context_menu(self, pos):
        patient_data = self.patients_view.get_selected_patient_data()
        if not patient_data:
            return

        context_menu = QMenu(self)
        folder_action = context_menu.addAction("🗂️ Ouvrir Dossier Patient") 
        context_menu.addSeparator() 
        follow_up_action = context_menu.addAction("➕ Nouveau Suivi") 
        edit_action = context_menu.addAction("✏️ Modifier les informations")
        delete_action = context_menu.addAction("🗑️ Supprimer le Patient") 

        action = context_menu.exec(self.patients_view.patient_table.mapToGlobal(pos))

        if action == folder_action:
            self.open_patient_folder_dialog(patient_data)
        elif action == follow_up_action:
            self.open_add_follow_up_dialog(patient_data)
        elif action == edit_action:
            self.open_edit_patient_dialog(patient_data)
        elif action == delete_action:
            self.confirm_delete_patient(patient_data)

    def logout(self):
        self.api_client.logout()
        if hasattr(self.parent(), 'show_login'):
            self.parent().show_login()
        self.close()