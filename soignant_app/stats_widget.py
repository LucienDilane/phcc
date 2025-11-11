# desktop_app/stats_widget.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class StatsWidget(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.init_ui()
        self.load_stats()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        title_label = QLabel("Tableau de Bord & Statistiques Clés")
        title_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        self.grid_layout = QGridLayout()
        main_layout.addLayout(self.grid_layout)
        
        # Initialisation des cartes de stats
        self.patient_card = self._create_stat_card("Total Patients", "...", "person")
        self.rdv_card = self._create_stat_card("RDV cette semaine", "...", "calendar")
        self.suivi_card = self._create_stat_card("Suivis (30 jours)", "...", "notes")
        
        self.grid_layout.addWidget(self.patient_card, 0, 0)
        self.grid_layout.addWidget(self.rdv_card, 0, 1)
        self.grid_layout.addWidget(self.suivi_card, 0, 2)
        
        main_layout.addStretch(1) # Pousser les cartes vers le haut

    def _create_stat_card(self, title, value, icon_name):
        frame = QFrame()
        frame.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 8px;")
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        value_label.setObjectName(f"{title.replace(' ', '_')}_value_label") # Pour mise à jour facile
        layout.addWidget(value_label)
        
        return frame

    def load_stats(self):
        success, data = self.api_client.get_global_stats()
        
        if success:
            self.findChild(QLabel, "Total_Patients_value_label").setText(str(data.get('total_patients', 0)))
            self.findChild(QLabel, "RDV_cette_semaine_value_label").setText(str(data.get('rdv_this_week', 0)))
            self.findChild(QLabel, "Suivis_(30_jours)_value_label").setText(str(data.get('suivis_last_month', 0)))
            
            # Vous pouvez ajouter ici la gestion des 'suivi_status_counts' dans un autre graphique/liste.
        else:
            QMessageBox.critical(self, "Erreur Statistiques", f"Impossible de charger les statistiques globales.\nErreur: {data.get('error', 'API non disponible')}")