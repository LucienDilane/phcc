# desktop_app/dashboard_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QSize
# Note: L'API client n'est pas utilisée directement dans ce widget pour l'instant
# from .utils.api_client import ApiClient 

# --- Définition des Couleurs Clés ---
COLOR_MAIN_GREEN = "#4CAF50"
COLOR_LIGHT_GREEN = "#E8F5E9"
COLOR_MAIN_TEXT = "#333333"

class DashboardWidget(QWidget):
    """
    Widget affichant le tableau de bord principal avec les actions clés.
    """
    def __init__(self, api_client=None, user_data=None, parent=None):
        super().__init__(parent)
        self.api_client = api_client 
        self.user_data = user_data
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 1. En-tête de bienvenue
        first_name = self.user_data.get('first_name', self.user_data.get('username'))
        welcome_label = QLabel(f"Bienvenue, Dr. {first_name} ! 👋")
        welcome_label.setStyleSheet(f"font-size: 24pt; color: {COLOR_MAIN_GREEN}; font-weight: bold;")
        
        status_label = QLabel("Tableau de bord des actions rapides.")
        status_label.setStyleSheet(f"font-size: 12pt; color: {COLOR_MAIN_TEXT}; margin-bottom: 20px;")
        
        main_layout.addWidget(welcome_label)
        main_layout.addWidget(status_label)
        
        # 2. Zone des Cartes d'Actions Rapides
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # Définition des actions (Nom, Icône/Emoji, Couleur, Slot de connexion futur)
        # Note : Ces cartes ne sont pas encore fonctionnelles, elles sont décoratives.
        actions = [
            ("Ajouter un nouveau Patient", "➕", "#1E88E5"), # Bleu
            ("Consulter l'Agenda", "🗓️", "#FFB300"),       # Jaune/Orange
            ("Rapports d'activité", "📈", "#D81B60"),      # Rose/Rouge
            ("Gérer les utilisateurs", "🧑‍⚕️", "#00ACC1"),   # Cyan
        ]

        for i, (text, icon, color) in enumerate(actions):
            card = self._create_action_card(text, icon, color)
            row = i // 2
            col = i % 2
            grid_layout.addWidget(card, row, col)

        main_layout.addLayout(grid_layout)
        main_layout.addStretch(1) # Pousse le contenu vers le haut

    def _create_action_card(self, text, icon, color):
        """Crée un widget cliquable stylisé pour une action."""
        
        card = QFrame()
        card.setFixedSize(QSize(300, 150))
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            }}
            QFrame:hover {{
                background-color: lighter({color}, 110%);
                border: 2px solid white;
            }}
            QLabel {{
                color: white;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 36pt;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(text)
        text_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(icon_label)
        card_layout.addWidget(text_label)
        
        return card