# soignant_app/config_management.py (Correction finale du constructeur et des appels API)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
    QLabel, QPushButton, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QHBoxLayout, QComboBox, 
    QGridLayout, QAbstractItemView, QDialog, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import Qt
import requests
import json 
import uuid 

# --- CLASSE : Dialogue pour ajouter une Question (Inchangée) ---

class QuestionDialog(QDialog):
    """Boîte de dialogue simple pour saisir les détails d'une question."""
    def __init__(self, parent=None, question_data=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter / Modifier une Question")
        self.question_data = question_data if question_data is not None else {}
        self.layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # ID Technique (pour le backend)
        self.id_input = QLineEdit(self)
        self.id_input.setReadOnly(True)
        if 'id' not in self.question_data:
            # Générer un ID court unique pour les nouvelles questions
            self.id_input.setText(str(uuid.uuid4())[:8]) 
        else:
            self.id_input.setText(self.question_data.get('id', ''))
            
        self.label_input = QLineEdit(self)
        self.type_combo = QComboBox(self)
        
        # Types de questions supportés
        self.type_combo.addItems([
            "TEXT", "PAIN", "YES_NO", "MED", "DATE"
        ])
        
        # Options désactivées pour l'interface simplifiée
        self.options_input = QLineEdit(self)
        self.options_input.setDisabled(True) 

        form.addRow("ID Technique :", self.id_input)
        form.addRow("Libellé de la question :", self.label_input)
        form.addRow("Type de Question :", self.type_combo)
        form.addRow("Options (Avancé) :", self.options_input)
        
        self.layout.addLayout(form)
        
        # Remplir si en mode édition
        if self.question_data:
            self.label_input.setText(self.question_data.get('label', ''))
            index = self.type_combo.findText(self.question_data.get('type', 'TEXT'))
            if index != -1:
                self.type_combo.setCurrentIndex(index)
        
        # Boutons OK et Annuler
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def get_data(self):
        """Retourne la structure de la question à insérer dans le JSON du questionnaire."""
        return {
            "id": self.id_input.text(),
            "type": self.type_combo.currentText(),
            "label": self.label_input.text()
        }

# --- CLASSE PRINCIPALE : ConfigManagementWidget ---

class ConfigManagementWidget(QWidget):
    """Widget de gestion des questionnaires avec éditeur visuel de structure."""
    # CORRECTION: Accepter 'headers' dans le constructeur
    def __init__(self, api_url, headers, parent=None): 
        super().__init__(parent)
        self.questionnaires_endpoint = api_url + "questionnaires/"
        self.headers = headers  # <-- Stocker les headers pour l'authentification
        self.current_questions_list = [] 
        self.current_q_id = None
        
        self.layout = QHBoxLayout(self)
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.layout.addWidget(self.list_widget, 1) 
        
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.layout.addWidget(self.form_widget, 3) 
        
        self.setup_ui()
        self.load_questionnaires()

    def setup_ui(self):
        # --- A. Configuration de la Liste ---
        self.list_layout.addWidget(QLabel("<h2>Questionnaires Enregistrés</h2>"))
        self.questionnaire_table = QTableWidget()
        self.questionnaire_table.setColumnCount(2)
        self.questionnaire_table.setHorizontalHeaderLabels(["ID", "Nom du Questionnaire"])
        self.questionnaire_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questionnaire_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.questionnaire_table.itemSelectionChanged.connect(self.load_selected_questionnaire)
        self.list_layout.addWidget(self.questionnaire_table)
        
        list_btn_layout = QHBoxLayout()
        
        # STYLE: Bouton Nouveau (Vert)
        self.new_btn = QPushButton("➕ Nouveau Questionnaire")
        self.new_btn.setObjectName("createButton")
        self.new_btn.clicked.connect(self.new_questionnaire)
        
        # STYLE: Bouton Actualiser (Bleu)
        self.refresh_btn = QPushButton("🔄 Actualiser")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.clicked.connect(self.load_questionnaires)
        
        list_btn_layout.addWidget(self.new_btn)
        list_btn_layout.addWidget(self.refresh_btn)
        self.list_layout.addLayout(list_btn_layout)


        # --- B. Configuration de l'Éditeur Visuel ---
        
        # Champs Nom et Description
        form_fields = QFormLayout()
        self.q_name = QLineEdit()
        self.q_desc = QLineEdit()
        form_fields.addRow("Nom :", self.q_name)
        form_fields.addRow("Description :", self.q_desc)
        
        self.form_layout.addWidget(QLabel("<h2>Détails du Questionnaire</h2>"))
        self.form_layout.addLayout(form_fields)
        
        # Éditeur de Questions
        self.form_layout.addWidget(QLabel("<h3>Structure des Questions</h3>"))
        
        question_controls = QHBoxLayout()
        
        # STYLE: Ajouter Question (Vert)
        self.add_q_btn = QPushButton("➕ Ajouter Question")
        self.add_q_btn.setObjectName("createButton")
        self.add_q_btn.clicked.connect(lambda: self.open_question_dialog())
        
        # STYLE: Modifier Question (Bleu)
        self.edit_q_btn = QPushButton("✏️ Modifier Question")
        self.edit_q_btn.setObjectName("saveButton")
        self.edit_q_btn.clicked.connect(lambda: self.open_question_dialog(edit_mode=True))
        
        # STYLE: Supprimer Question (Rouge)
        self.delete_q_btn = QPushButton("🗑️ Supprimer Question")
        self.delete_q_btn.setObjectName("deleteButton")
        self.delete_q_btn.clicked.connect(self.delete_selected_question)

        question_controls.addWidget(self.add_q_btn)
        question_controls.addWidget(self.edit_q_btn)
        question_controls.addWidget(self.delete_q_btn)
        self.form_layout.addLayout(question_controls)

        self.questions_table = QTableWidget()
        self.questions_table.setColumnCount(3)
        self.questions_table.setHorizontalHeaderLabels(["ID", "Type", "Libellé"])
        self.questions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.questions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.questions_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) 
        self.form_layout.addWidget(self.questions_table)
        
        # Boutons Sauvegarder et Supprimer Questionnaire
        # STYLE: Sauvegarder Questionnaire (Bleu)
        self.save_btn = QPushButton("💾 Sauvegarder Questionnaire (POST/PATCH)")
        self.save_btn.setObjectName("saveButton")
        self.save_btn.clicked.connect(self.save_questionnaire)
        self.form_layout.addWidget(self.save_btn)
        
        # STYLE: Supprimer TOUT (Rouge)
        self.delete_q_master_btn = QPushButton("🗑️ Supprimer TOUT le Questionnaire")
        self.delete_q_master_btn.setObjectName("deleteButton")
        self.delete_q_master_btn.setEnabled(False)
        self.delete_q_master_btn.clicked.connect(self.delete_questionnaire)
        self.form_layout.addWidget(self.delete_q_master_btn)
        self.form_layout.addStretch()

    # --- LOGIQUE D'INTERFACE ET GESTION DES QUESTIONS (Inchangée) ---
    
    def new_questionnaire(self):
        """Réinitialise le formulaire pour une nouvelle création."""
        self.current_q_id = None
        self.current_questions_list = []
        self.q_name.clear()
        self.q_desc.clear()
        self.delete_q_master_btn.setEnabled(False)
        self.questionnaire_table.clearSelection()
        self._update_questions_table()

    def _update_questions_table(self):
        """Met à jour le QTableWidget à partir de self.current_questions_list."""
        self.questions_table.setRowCount(len(self.current_questions_list))
        
        for row, q in enumerate(self.current_questions_list):
            self.questions_table.setItem(row, 0, QTableWidgetItem(q['id']))
            self.questions_table.setItem(row, 1, QTableWidgetItem(q['type']))
            self.questions_table.setItem(row, 2, QTableWidgetItem(q['label']))


    def open_question_dialog(self, edit_mode=False):
        """Ouvre la boîte de dialogue pour ajouter ou modifier une question."""
        initial_data = {}
        target_row = -1
        
        if edit_mode:
            selected_rows = self.questions_table.selectedIndexes()
            if not selected_rows:
                QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une question à modifier.")
                return
            
            target_row = selected_rows[0].row()
            initial_data = self.current_questions_list[target_row] 

        dialog = QuestionDialog(self, question_data=initial_data)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data['label']:
                 QMessageBox.warning(self, "Erreur", "Le libellé de la question ne peut être vide.")
                 return
                 
            if edit_mode and target_row != -1:
                # Modification
                self.current_questions_list[target_row] = new_data
            else:
                # Ajout
                self.current_questions_list.append(new_data)
                
            self._update_questions_table()


    def delete_selected_question(self):
        """Supprime la question sélectionnée du questionnaire en cours d'édition."""
        selected_rows = self.questions_table.selectedIndexes()
        if not selected_rows:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner une question à supprimer.")
            return

        target_row = selected_rows[0].row()
        
        reply = QMessageBox.question(self, 'Confirmation', 
            "Êtes-vous sûr de vouloir supprimer cette question ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.current_questions_list[target_row]
            self._update_questions_table()
            
            
    # --- LOGIQUE API (Mise à jour pour utiliser self.headers) ---
    
    def load_questionnaires(self):
        """Récupère et affiche la liste des questionnaires depuis l'API."""
        self.questionnaire_table.setRowCount(0)
        try:
            # MISE À JOUR: Utiliser self.headers pour l'authentification
            response = requests.get(self.questionnaires_endpoint, headers=self.headers) 
            if response.status_code == 200:
                questionnaires = response.json()
                self.questionnaire_table.setRowCount(len(questionnaires))
                for row, q in enumerate(questionnaires):
                    self.questionnaire_table.setItem(row, 0, QTableWidgetItem(str(q['id'])))
                    self.questionnaire_table.setItem(row, 1, QTableWidgetItem(q['nom']))
        except Exception:
            QMessageBox.critical(self, "Erreur Réseau", "Impossible de charger les questionnaires.")

    def load_selected_questionnaire(self):
        """Charge les détails du questionnaire sélectionné dans le formulaire."""
        selected_rows = self.questionnaire_table.selectedIndexes()
        if not selected_rows:
            self.delete_q_master_btn.setEnabled(False)
            return

        q_id = self.questionnaire_table.item(selected_rows[0].row(), 0).text()
        self.delete_q_master_btn.setEnabled(True)
        
        try:
            # MISE À JOUR: Utiliser self.headers
            response = requests.get(self.questionnaires_endpoint + q_id + "/", headers=self.headers)
            if response.status_code == 200:
                q_data = response.json()
                self.current_q_id = q_data['id']
                self.q_name.setText(q_data['nom'])
                self.q_desc.setText(q_data['description'])
                
                # Remplir la liste Python à partir du JSON du backend
                self.current_questions_list = q_data['structure_json']
                self._update_questions_table()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de charger les détails.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement : {e}")

    def save_questionnaire(self):
        """Sauvegarde ou modifie le questionnaire via POST/PATCH."""
        
        if not self.q_name.text() or not self.current_questions_list:
            QMessageBox.warning(self, "Erreur de Saisie", "Le Nom et au moins une Question sont obligatoires.")
            return
            
        data = {
            "nom": self.q_name.text(),
            "description": self.q_desc.text(),
            "structure_json": self.current_questions_list 
        }
        
        try:
            headers = self.headers 
            
            if self.current_q_id: # Modification (PATCH)
                url = self.questionnaires_endpoint + str(self.current_q_id) + "/"
                response = requests.patch(url, data=json.dumps(data), headers=headers)
                msg = "modifié"
            else: # Création (POST)
                url = self.questionnaires_endpoint
                response = requests.post(url, data=json.dumps(data), headers=headers)
                msg = "créé"
            
            if response.status_code in [200, 201]:
                QMessageBox.information(self, "Succès", f"Questionnaire {msg} avec succès.")
                self.load_questionnaires()
                if response.status_code == 201:
                    self.new_questionnaire()
            else:
                QMessageBox.critical(self, "Erreur API", f"Échec de la sauvegarde: {response.json()}")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur Réseau", "Serveur Django injoignable.")


    def delete_questionnaire(self):
        """Supprime le questionnaire sélectionné."""
        if not self.current_q_id: return
        reply = QMessageBox.question(self, 'Confirmation', 
            f"Êtes-vous sûr de vouloir supprimer le Questionnaire ID {self.current_q_id} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                url = self.questionnaires_endpoint + str(self.current_q_id) + "/"
                # MISE À JOUR: Utiliser self.headers
                response = requests.delete(url, headers=self.headers)
                
                if response.status_code == 204:
                    QMessageBox.information(self, "Succès", "Questionnaire supprimé.")
                    self.new_questionnaire()
                    self.load_questionnaires()
                else:
                    QMessageBox.critical(self, "Erreur API", f"Échec de la suppression: {response.json()}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de suppression: {e}")