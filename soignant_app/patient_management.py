# soignant_app/patient_management.py (Version finale - Corrigé et Stylisé)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QLabel, QPushButton, QMessageBox, QDateEdit, 
    QTableWidget, QTableWidgetItem, QHBoxLayout, 
    QHeaderView, QComboBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import QDate, Qt
import requests
import json 
import string
import random

# --- Utilities (Inchangé) ---
def generate_random_password(length=12):
    """Génère un mot de passe aléatoire pour le patient."""
    characters = string.ascii_letters + string.digits + '!@#$'
    return ''.join(random.choice(characters) for i in range(length))
# ----------------------------

class PatientManagementWidget(QWidget):
    def __init__(self, api_url, auth_token, parent=None): 
        super().__init__(parent)
        self.api_url = api_url 
        self.auth_token = auth_token
        
        # En-têtes pour toutes les requêtes authentifiées
        self.auth_headers = {'Authorization': f'Token {self.auth_token}', 
                             'Content-Type': 'application/json'}
                             
        self.patients_endpoint = api_url + "patients/"
        self.plans_endpoint = api_url + "plans/"
        self.questionnaires_endpoint = api_url + "questionnaires/"
        
        self.current_editing_patient_id = None
        self.current_editing_plan_id = None
        
        self.main_layout = QVBoxLayout(self)
        self.patients_data = {}
        
        self.setup_ui()
        self.load_questionnaires() # <--- Le chargement est appelé ici
        self.load_patients()

    def setup_ui(self):
        
        # 1. Zone de Sélection du Patient (Liste compacte)
        self.main_layout.addWidget(QLabel("<h2>1. Sélection du Patient</h2>"))
        
        list_controls = QHBoxLayout()
        list_controls.addWidget(QLabel("<b>Cliquez sur une ligne pour modifier:</b>"))
        self.add_new_btn = QPushButton("➕ Créer un Nouveau Patient")
        self.add_new_btn.clicked.connect(self.start_new_patient_creation)
        list_controls.addWidget(self.add_new_btn)
        # Bouton d'actualisation de la liste des patients, mais nous allons aussi actualiser la liste des Q.
        list_controls.addWidget(QPushButton("🔄 Actualiser la Liste", clicked=self.load_patients)) 
        self.main_layout.addLayout(list_controls)
        
        self.patient_table = QTableWidget()
        self.patient_table.setColumnCount(4)
        self.patient_table.setHorizontalHeaderLabels(["ID", "Initiales", "Nom", "Prénom"])
        self.patient_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.patient_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.patient_table.itemSelectionChanged.connect(self.load_selected_patient_for_edit)
        self.patient_table.setFixedHeight(200) # Compact pour la sélection
        self.main_layout.addWidget(self.patient_table)

        # 2. Zone de Saisie du Formulaire
        self.main_layout.addWidget(QLabel("<h2>2. Détails Patient et Plan</h2>"))
        self._setup_creation_form() # Le formulaire principal est toujours visible


    def _setup_creation_form(self):
        """Définit l'interface du formulaire principal (Création/Modification)."""
        
        # Conteneur pour séparer les champs Patient et Plan sur la même ligne
        container = QWidget()
        grid_layout = QGridLayout(container)
        
        # --- A. Formulaire Patient (Colonne 0) ---
        patient_group = QWidget()
        patient_form = QFormLayout(patient_group)
        self.initiales_input = QLineEdit()
        self.nom_input = QLineEdit()
        self.prenom_input = QLineEdit()
        self.date_naissance_input = QDateEdit(calendarPopup=True)
        self.date_naissance_input.setDate(QDate.currentDate().addYears(-30))
        self.contact_urgence_input = QLineEdit()
        self.telephone_input = QLineEdit()
        self.email_input = QLineEdit()

        patient_form.addRow("Initiales (Soignant):", self.initiales_input)
        patient_form.addRow("Nom:", self.nom_input)
        patient_form.addRow("Prénom:", self.prenom_input)
        patient_form.addRow("Date de Naissance:", self.date_naissance_input)
        patient_form.addRow("Contact d'Urgence:", self.contact_urgence_input)
        patient_form.addRow("Téléphone (PII):", self.telephone_input)
        patient_form.addRow("Email (PII):", self.email_input)
        
        grid_layout.addWidget(QLabel("<b>Informations Personnelles</b>"), 0, 0)
        grid_layout.addWidget(patient_group, 1, 0)
        
        # --- B. Formulaire Plan de Suivi (Colonne 1) ---
        plan_group = QWidget()
        plan_form = QFormLayout(plan_group)
        
        self.questionnaires_list = QComboBox()
        self.create_questionnaire_btn = QPushButton("Créer Questionnaire par Défaut (Si vide)")
        self.create_questionnaire_btn.clicked.connect(self.create_simple_questionnaire)
        
        self.date_debut_input = QDateEdit(calendarPopup=True)
        self.date_debut_input.setDate(QDate.currentDate())
        self.date_fin_input = QDateEdit(calendarPopup=True)
        self.date_fin_input.setDate(QDate.currentDate().addMonths(1))
        self.instructions_input = QLineEdit()
        
        plan_form.addRow("Questionnaire Assigné:", self.questionnaires_list)
        plan_form.addRow("", self.create_questionnaire_btn)
        plan_form.addRow("Date de Début:", self.date_debut_input)
        plan_form.addRow("Date de Fin:", self.date_fin_input)
        plan_form.addRow("Instructions Spécifiques:", self.instructions_input)
        
        grid_layout.addWidget(QLabel("<b>Plan de Suivi</b>"), 0, 1)
        grid_layout.addWidget(plan_group, 1, 1)

        self.main_layout.addWidget(container)
        
        # Bouton Final de Soumission
        self.submit_button = QPushButton("✅ ENREGISTRER / CRÉER PATIENT ET PLAN")
        self.submit_button.setFixedHeight(40)
        self.submit_button.clicked.connect(self.handle_submit)
        self.main_layout.addWidget(self.submit_button)
        
        # Bouton de Suppression (séparé pour la clarté)
        self.delete_btn = QPushButton("🗑️ Supprimer le Patient sélectionné")
        self.delete_btn.clicked.connect(self.delete_selected_patient)
        self.delete_btn.setEnabled(False) # Désactivé par défaut
        self.main_layout.addWidget(self.delete_btn)
        
        self.main_layout.addStretch()

    # --- LOGIQUE DE FLUX INTUITIF ---
    
    def start_new_patient_creation(self):
        """Réinitialise le formulaire pour la création d'un nouveau patient."""
        self.clear_form()
        self.current_editing_patient_id = None
        self.current_editing_plan_id = None
        self.patient_table.clearSelection()
        self.submit_button.setText("✅ CRÉER NOUVEAU PATIENT ET PLAN")
        self.delete_btn.setEnabled(False)


    def load_selected_patient_for_edit(self):
        """Charge les données du patient sélectionné dans le formulaire pour modification."""
        selected_rows = self.patient_table.selectedIndexes()
        if not selected_rows:
            self.start_new_patient_creation()
            return
        
        patient_id = self.patient_table.item(selected_rows[0].row(), 0).text()
        self.current_editing_patient_id = patient_id
        
        try:
            # 1. Récupérer les données du Patient
            patient_url = self.patients_endpoint + patient_id + "/"
            response = requests.get(patient_url, headers=self.auth_headers) # AUTH
            if response.status_code != 200:
                QMessageBox.critical(self, "Erreur API", "Impossible de charger les détails du patient.")
                self.start_new_patient_creation()
                return

            patient_data = response.json()
            
            # Gestion robuste du champ 'details'
            details_data = patient_data.get('details') or {} 
            
            # 2. Récupérer le plan de suivi actif
            plan_url = self.plans_endpoint + f"?patient={patient_id}&actif=true"
            plan_response = requests.get(plan_url, headers=self.auth_headers) # AUTH
            current_plan = plan_response.json()[0] if plan_response.status_code == 200 and plan_response.json() else {}

            # Remplir le formulaire
            self.clear_form()
            self.submit_button.setText(f"💾 ENREGISTRER MODIFICATIONS (ID: {patient_id})")
            self.delete_btn.setEnabled(True)
            
            self.initiales_input.setText(patient_data.get('initiales', ''))
            self.nom_input.setText(details_data.get('nom', ''))
            self.prenom_input.setText(details_data.get('prenom', ''))
            self.date_naissance_input.setDate(QDate.fromString(patient_data.get('date_naissance'), "yyyy-MM-dd"))
            self.contact_urgence_input.setText(patient_data.get('contact_urgence', ''))
            self.telephone_input.setText(details_data.get('telephone', ''))
            self.email_input.setText(details_data.get('email', ''))
            
            # Remplissage des champs Plan
            if current_plan:
                self.current_editing_plan_id = current_plan.get('id')
                
                # --- SÉLECTION DU QUESTIONNAIRE ACTIF ---
                # Trouve l'index dans la liste déroulante basé sur l'ID du questionnaire
                index = self.questionnaires_list.findData(current_plan.get('questionnaire'))
                if index >= 0:
                    self.questionnaires_list.setCurrentIndex(index)
                    
                self.date_debut_input.setDate(QDate.fromString(current_plan.get('date_debut'), "yyyy-MM-dd"))
                self.date_fin_input.setDate(QDate.fromString(current_plan.get('date_fin'), "yyyy-MM-dd"))
                self.instructions_input.setText(current_plan.get('instructions', ''))
            else:
                self.current_editing_plan_id = None
                QMessageBox.information(self, "Plan", "Ce patient n'a pas de plan actif.")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur Réseau", "Serveur Django injoignable.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Erreur de chargement: {e}")


    def handle_submit(self):
        """Déclenche la création ou la modification selon l'état."""
        if self.current_editing_patient_id:
            self.save_patient_modifications(
                self.current_editing_patient_id, 
                self.current_editing_plan_id
            )
        else:
            self.create_patient_and_plan()

    # --- LOGIQUE API ---
    
    def load_patients(self):
        """Récupère et affiche la liste des patients depuis l'API."""
        try:
            response = requests.get(self.patients_endpoint, headers=self.auth_headers) # AUTH
            if response.status_code == 200:
                patients = response.json()
                self.patient_table.setRowCount(len(patients))
                
                for row, p in enumerate(patients):
                    
                    # Gestion robuste du champ 'details'
                    details = p.get('details') or {} 
                    
                    self.patient_table.setItem(row, 0, QTableWidgetItem(str(p['id'])))
                    self.patient_table.setItem(row, 1, QTableWidgetItem(p['initiales']))
                    self.patient_table.setItem(row, 2, QTableWidgetItem(details.get('nom', 'N/A')))
                    self.patient_table.setItem(row, 3, QTableWidgetItem(details.get('prenom', 'N/A')))
                    
            else:
                QMessageBox.critical(self, "Erreur API", "Impossible de charger les patients. (Erreur Auth/Serveur)")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur Réseau", "Serveur Django injoignable.")


    def load_questionnaires(self):
        """
        Charge la liste de TOUS les questionnaires depuis l'API et met à jour le QComboBox.
        """
        self.questionnaires_list.clear() # <-- Vider la liste est CRUCIAL
        try:
            url = self.questionnaires_endpoint
            response = requests.get(url, headers=self.auth_headers) # AUTH
            
            if response.status_code == 200:
                data = response.json()
                self.questionnaires_data = {}
                for q in data:
                    # AJOUT DE TOUS LES QUESTIONNAIRES
                    self.questionnaires_list.addItem(q['nom'], q['id']) 
                    self.questionnaires_data[q['id']] = q
                    
                if not data:
                    self.questionnaires_list.addItem("Aucun questionnaire trouvé. Créez-en un.")
            else:
                QMessageBox.warning(self, "Erreur API", "Échec du chargement des questionnaires.")
                
        except requests.exceptions.ConnectionError:
            self.questionnaires_list.addItem("Erreur de connexion à l'API.")

    def create_simple_questionnaire(self):
        """Crée un questionnaire par défaut 'Suivi de la douleur' pour la démo."""
        questionnaire_data = {
            "nom": "Suivi Douleur Quotidien",
            "description": "Évaluation de la douleur (1-10) et prise de médicaments.",
            "structure_json": [
                {"id": "douleur", "type": "PAIN", "label": "Quel est votre niveau de douleur (1-10)?"},
                {"id": "medicament", "type": "MED", "label": "Avez-vous pris vos médicaments aujourd'hui?"},
                {"id": "notes", "type": "TEXT", "label": "Notes supplémentaires (optionnel)"}
            ]
        }
        
        try:
            url = self.questionnaires_endpoint
            response = requests.post(
                url, 
                data=json.dumps(questionnaire_data),
                headers=self.auth_headers # AUTH
            )
            
            if response.status_code == 201:
                QMessageBox.information(self, "Succès", "Questionnaire créé.")
                self.load_questionnaires()
            else:
                QMessageBox.critical(self, "Erreur Création Q.", f"Échec: {response.json()}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la création du questionnaire: {e}")

    def create_patient_and_plan(self):
        """1. Crée le Patient, puis 2. Assigne le Plan de Suivi."""
        
        patient_data = {
            "initiales": self.initiales_input.text(),
            "date_naissance": self.date_naissance_input.date().toString("yyyy-MM-dd"),
            "contact_urgence": self.contact_urgence_input.text(),
            "details": {
                "nom": self.nom_input.text(),
                "prenom": self.prenom_input.text(),
                "telephone": self.telephone_input.text(),
                "email": self.email_input.text(),
            }
        }

        if not patient_data["initiales"] or not patient_data["details"]["nom"]:
             QMessageBox.warning(self, "Erreur de Saisie", "Les champs Initiales et Nom sont obligatoires.")
             return

        try:
            # Envoi de la requête POST pour créer le patient
            response = requests.post(
                self.patients_endpoint, 
                data=json.dumps(patient_data),
                headers=self.auth_headers # AUTH
            )
            
            if response.status_code != 201:
                QMessageBox.critical(self, "Erreur Patient", f"Échec de la création du patient: {response.json()}")
                return

            patient_response = response.json()
            new_patient_id = patient_response['id']
            
            plain_password = patient_response.get('plain_password', 'N/A')
            details_response = patient_response.get('details', {})
            login_id = details_response.get('login_id', 'N/A')

            # --- 2. Assignation du Plan de Suivi ---
            questionnaire_id = self.questionnaires_list.currentData()
            
            if not questionnaire_id:
                QMessageBox.warning(self, "Attention", "Patient créé. Aucun questionnaire sélectionné, plan non assigné.")
                self.start_new_patient_creation()
                self.load_patients()
                return

            # Correction pour le champ 'instructions' : garantir une chaîne non vide
            plan_data = {
                "patient": new_patient_id,
                "questionnaire": questionnaire_id,
                "date_debut": self.date_debut_input.date().toString("yyyy-MM-dd"),
                "date_fin": self.date_fin_input.date().toString("yyyy-MM-dd"),
                "instructions": self.instructions_input.text().strip() or "Aucune", 
                "actif": True
            }
            
            plan_response = requests.post(
                self.plans_endpoint, 
                data=json.dumps(plan_data),
                headers=self.auth_headers # AUTH
            )
            
            if plan_response.status_code == 201:
                # AFFICHAGE DU LOGIN ET MOT DE PASSE CLAIR
                QMessageBox.information(
                    self, 
                    "Succès Total !", 
                    f"Patient ID {new_patient_id} créé et plan assigné.\n\n"
                    f"INFORMATIONS DE CONNEXION PATIENT (À NOTER DANS LE CARNET MÉDICAL):\n"
                    f"ID de Connexion: 🔑 {login_id}\n"
                    f"Mot de Passe: 🔒 {plain_password}\n\n"
                    f"NOTE: Transmettez ces informations au patient."
                )
                self.start_new_patient_creation()
                self.load_patients()
            else:
                QMessageBox.critical(self, "Erreur Plan", f"Patient créé, mais échec de l'assignation du plan: {plan_response.json()}")
                
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur Réseau", "Impossible de se connecter au serveur Django.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Une erreur s'est produite: {e}")

    def save_patient_modifications(self, patient_id, plan_id=None):
        """Met à jour le Patient (PUT/PATCH) et son Plan de Suivi (PUT/POST)."""

        patient_data_to_save = {
            "initiales": self.initiales_input.text(),
            "date_naissance": self.date_naissance_input.date().toString("yyyy-MM-dd"),
            "contact_urgence": self.contact_urgence_input.text(),
            "details": {
                "nom": self.nom_input.text(),
                "prenom": self.prenom_input.text(),
                "telephone": self.telephone_input.text(),
                "email": self.email_input.text(),
            }
        }
        
        try:
            # Requête PATCH pour mettre à jour le patient
            patient_url = self.patients_endpoint + patient_id + "/"
            response = requests.patch(
                patient_url, 
                data=json.dumps(patient_data_to_save),
                headers=self.auth_headers # AUTH
            )
            
            if response.status_code not in [200, 204]: 
                QMessageBox.critical(self, "Erreur Modif Patient", f"Échec de la modification du patient: {response.json()}")
                return

            # 2. Mise à jour/Création du Plan de Suivi
            questionnaire_id = self.questionnaires_list.currentData()

            # Correction pour le champ 'instructions' : garantir une chaîne non vide
            plan_data = {
                "patient": int(patient_id),
                "questionnaire": questionnaire_id,
                "date_debut": self.date_debut_input.date().toString("yyyy-MM-dd"),
                "date_fin": self.date_fin_input.date().toString("yyyy-MM-dd"),
                "instructions": self.instructions_input.text().strip() or "Aucune", 
                "actif": True
            }

            if plan_id:
                # Modification d'un plan existant (PUT)
                plan_url = self.plans_endpoint + str(plan_id) + "/"
                plan_response = requests.put(
                    plan_url, 
                    data=json.dumps(plan_data),
                    headers=self.auth_headers # AUTH
                )
            else:
                # Création d'un nouveau plan (POST)
                plan_url = self.plans_endpoint
                plan_response = requests.post(
                    plan_url, 
                    data=json.dumps(plan_data),
                    headers=self.auth_headers # AUTH
                )

            if plan_response.status_code in [200, 201]:
                QMessageBox.information(self, "Succès Total", f"Patient ID {patient_id} et Plan de Suivi mis à jour.")
                self.start_new_patient_creation()
                self.load_patients()
            else:
                QMessageBox.critical(self, "Erreur Modif Plan", f"Patient modifié, mais échec du plan: {plan_response.json()}")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur Réseau", "Serveur Django injoignable.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inattendue", f"Erreur: {e}")


    def delete_selected_patient(self):
        """Supprime le patient sélectionné de la base de données via l'API."""
        if not self.current_editing_patient_id:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un patient à supprimer.")
            return

        patient_id = self.current_editing_patient_id
        
        reply = QMessageBox.question(
            self, 'Confirmation', 
            f"Êtes-vous sûr de vouloir supprimer le Patient ID {patient_id} ?\n"
            "Toutes ses données de suivi seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                url = self.patients_endpoint + patient_id + "/"
                response = requests.delete(url, headers=self.auth_headers) # AUTH
                
                if response.status_code == 204: 
                    QMessageBox.information(self, "Succès", f"Patient ID {patient_id} supprimé.")
                    self.start_new_patient_creation()
                    self.load_patients() 
                else:
                    QMessageBox.critical(self, "Erreur API", f"Échec de la suppression: {response.json()}")

            except requests.exceptions.ConnectionError:
                QMessageBox.critical(self, "Erreur Réseau", "Serveur Django injoignable.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur Inattendue", f"Erreur: {e}")

    def clear_form(self):
        """Réinitialise tous les champs du formulaire."""
        self.initiales_input.clear()
        self.nom_input.clear()
        self.prenom_input.clear()
        self.contact_urgence_input.clear()
        self.telephone_input.clear()
        self.email_input.clear()
        self.date_naissance_input.setDate(QDate.currentDate().addYears(-30))
        self.date_debut_input.setDate(QDate.currentDate())
        self.date_fin_input.setDate(QDate.currentDate().addMonths(1))
        self.instructions_input.clear()