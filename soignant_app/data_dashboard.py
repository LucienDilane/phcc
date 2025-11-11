# soignant_app/data_dashboard.py

import requests
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, 
    QGridLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt

class DataDashboardWidget(QWidget):
    """
    Widget affichant le tableau de bord des données (résumés, statistiques).
    """
    def __init__(self, api_url, headers, parent=None):
        super().__init__(parent)
        
        self.api_url = api_url
        self.auth_headers = headers
        
        self._setup_ui()
        self.load_summary_data() 
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel("<h2>Tableau de Bord du Suivi</h2>"))
        
        # Résumé général
        summary_group = QGroupBox("Statistiques Générales")
        self.summary_layout = QGridLayout(summary_group)
        
        self.label_patients_count = QLabel("Patients actifs: Chargement...")
        self.label_plans_count = QLabel("Plans de suivi actifs: Chargement...")
        
        self.summary_layout.addWidget(self.label_patients_count, 0, 0)
        self.summary_layout.addWidget(self.label_plans_count, 0, 1)
        
        main_layout.addWidget(summary_group)

        # Tableau des dernières réponses
        recent_group = QGroupBox("Dernières Réponses Patients")
        recent_layout = QVBoxLayout(recent_group)
        self.response_table = QTableWidget(0, 4) # Patient, Question, Réponse, Date
        self.response_table.setHorizontalHeaderLabels(["Patient", "Question", "Réponse", "Date"])
        self.response_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        recent_layout.addWidget(self.response_table)
        main_layout.addWidget(recent_group)
        
        main_layout.addStretch()


    def load_summary_data(self):
        """
        Charge les données récapitulatives de l'API.
        """
        summary_url = f"{self.api_url}dashboard/summary/"
        
        try:
            response = requests.get(summary_url, headers=self.auth_headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Mise à jour de l'interface
            self.label_patients_count.setText(f"Patients actifs: {data.get('patients_count', 0)}")
            self.label_plans_count.setText(f"Plans de suivi actifs: {data.get('plans_count', 0)}")
            
            self.update_response_table(data.get('recent_responses', []))

        except requests.exceptions.RequestException as e:
            error_message = f"Erreur de connexion/serveur: {e}"
            print(f"Erreur de chargement du tableau de bord: {e}")
            self.label_patients_count.setText("Patients actifs: ERREUR")
            self.label_plans_count.setText("Plans de suivi actifs: ERREUR")
            QMessageBox.critical(self, "Erreur Tableau de Bord", error_message)

    def update_response_table(self, responses):
        """Met à jour le tableau avec les dernières réponses."""
        self.response_table.setRowCount(len(responses))
        for row, resp in enumerate(responses):
            self.response_table.setItem(row, 0, QTableWidgetItem(resp.get('patient_name', 'Inconnu')))
            self.response_table.setItem(row, 1, QTableWidgetItem(resp.get('question_text', 'N/A')))
            self.response_table.setItem(row, 2, QTableWidgetItem(str(resp.get('answer_value', ''))))
            self.response_table.setItem(row, 3, QTableWidgetItem(resp.get('timestamp', 'N/A')))