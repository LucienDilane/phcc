from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, 
    QListWidget, QListWidgetItem, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

class PatientSearchDialog(QDialog):
    """Dialogue pour rechercher un patient par nom, prénom ou identifiant."""
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("Rechercher un Patient pour RDV")
        self.selected_patient_data = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 1. Champ de recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Entrez le nom, prénom ou identifiant unique du patient...")
        
        self.search_button = QPushButton("🔍 Rechercher")
        self.search_button.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)
        
        # Connexion pour lancer la recherche en appuyant sur Entrée
        self.search_input.returnPressed.connect(self.perform_search)
        
        # 2. Liste des résultats
        main_layout.addWidget(QLabel("Résultats : Double-cliquez pour sélectionner"))
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.select_patient)
        main_layout.addWidget(self.results_list)

        # 3. Boutons d'action (Sélectionner/Annuler)
        self.select_final_button = QPushButton("Sélectionner le Patient")
        self.select_final_button.setEnabled(False) # Désactivé tant qu'aucun patient n'est sélectionné
        self.select_final_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.select_final_button)
        main_layout.addLayout(button_layout)
        
        self.results_list.currentItemChanged.connect(self._toggle_select_button)

    def _toggle_select_button(self):
        """Active le bouton 'Sélectionner' si un élément est choisi."""
        self.select_final_button.setEnabled(self.results_list.currentItem() is not None)


    def perform_search(self):
        """Appelle l'API pour rechercher des patients et affiche les résultats."""
        query = self.search_input.text().strip()
        self.results_list.clear()
        
        if not query:
            QMessageBox.warning(self, "Champ vide", "Veuillez entrer un terme de recherche.")
            return

        # 🚨 Appel API : Nous supposons que vous avez un endpoint /api/patients/?search=... 🚨
        # Vous devez ajouter cette méthode à votre ApiClient
        success, patients = self.api_client.search_patients(query)

        if success:
            if not patients:
                self.results_list.addItem("Aucun patient trouvé correspondant à la recherche.")
                return
            
            for patient in patients:
                # Utiliser l'identifiant pour l'affichage
                display_text = f"[{patient.get('username', 'ID N/A')}] - {patient.get('first_name')} {patient.get('last_name')} (Tél: {patient.get('telephone', 'N/A')})"
                item = QListWidgetItem(display_text)
                
                # Stocker les données complètes dans le rôle 'data' de l'item
                item.setData(Qt.ItemDataRole.UserRole, patient) 
                self.results_list.addItem(item)
        else:
            error_msg = patients.get('error', 'Erreur de recherche inconnue')
            QMessageBox.critical(self, "Erreur API", f"Échec de la recherche de patients: {error_msg}")


    def select_patient(self, item):
        """Sélectionne le patient à partir du double-clic et ferme le dialogue."""
        self.selected_patient_data = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
        
    def get_selected_patient(self):
        """Retourne les données du patient sélectionné."""
        return self.selected_patient_data