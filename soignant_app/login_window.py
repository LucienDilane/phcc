# desktop_app/login_window.py (Correction du ValueError)

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from .main import MainWindow 
from .utils.api_client import ApiClient

# --- Définition des Couleurs Clés (Cohérentes avec main_window.py) ---
COLOR_PRIMARY = "#2E7D32"      
COLOR_ACCENT = "#4CAF50"       
COLOR_TEXT_DARK = "#333333"    
COLOR_DANGER_RED = "#C62828"    
COLOR_NAVBAR_BG = "#1B5E20"     

class LoginWindow(QMainWindow):
    """
    Fenêtre de connexion pour l'application de bureau.
    """
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setWindowTitle("People Health Centre - Connexion")
        self.setFixedSize(400, 500) 
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 1. Titre/Logo
        title_label = QLabel("People Health Centre")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"font-size: 20pt; font-weight: bold; color: {COLOR_NAVBAR_BG}; margin-bottom: 20px;")
        
        # Sous-titre
        subtitle_label = QLabel("Accès Personnel Médical")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"font-size: 14pt; color: {COLOR_TEXT_DARK}; margin-bottom: 15px;")
        
        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)
        
        # 2. Champs de saisie
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur (Login)")
        self.username_input.setStyleSheet("padding: 12px; border: 1px solid #AAA; border-radius: 5px; font-size: 11pt;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 12px; border: 1px solid #AAA; border-radius: 5px; font-size: 11pt;")
        
        main_layout.addWidget(self.username_input)
        main_layout.addWidget(self.password_input)
        
        # 3. Bouton de Connexion
        self.login_button = QPushButton("Se Connecter")
        self.login_button.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {COLOR_ACCENT}; 
                color: white; 
                padding: 12px; 
                border-radius: 5px; 
                font-size: 12pt; 
                font-weight: bold; 
                margin-top: 10px;
            }}
            QPushButton:hover {{ 
                background-color: {COLOR_PRIMARY}; 
            }}
        """)
        self.login_button.clicked.connect(self.login)
        
        main_layout.addWidget(self.login_button)
        main_layout.addStretch(1) 
        
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

    def login(self):
        """
        Tente de connecter l'utilisateur en appelant l'API.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Erreur de Saisie", "Veuillez entrer le nom d'utilisateur et le mot de passe.")
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        # 🚨 CORRECTION DU VALUERROR
        # On appelle la méthode et on met le résultat dans une variable temporaire.
        result = self.api_client.login(username, password)
        
        QApplication.restoreOverrideCursor()

        # Si l'API client ne retourne qu'un dictionnaire, nous devons vérifier 
        # si ce dictionnaire contient un champ 'error' ou 'detail' pour déterminer le succès.
        
        if isinstance(result, tuple) and len(result) == 2:
            # Cas où l'API client retourne (success, data)
            success, response_data = result
        elif isinstance(result, dict):
            # Cas où l'API client retourne seulement un dictionnaire (user_data ou error_data)
            response_data = result
            # Supposons le succès si les données utilisateur sont présentes (ex: 'token', 'id')
            success = 'token' in response_data and 'id' in response_data
        else:
            # Cas inattendu
            response_data = {'detail': 'Réponse de l\'API inattendue.'}
            success = False

        if success:
            self.handle_login_success(response_data)
        else:
            self.handle_login_failure(response_data)


    def handle_login_success(self, response_data):
        api_token = response_data.get('token')
        user_data = response_data.get('user', {})
        
        if api_token:
            self.api_client.set_token(api_token)
            QMessageBox.information(self, "SUCCÈS", f"Connexion réussie. Bienvenue, {user_data.get('first_name', user_data.get('username'))}.")
        
        # 1. Création de la MainWindow
            self.main_window = MainWindow(api_client=self.api_client, user_data=user_data, parent=None)
            self.main_window.show()
        
        # 2. Fermeture de la fenêtre de login
            self.close()

    def handle_login_failure(self, error_data):
        """
        Gère l'échec de la connexion et affiche un message d'erreur.
        """
        if isinstance(error_data, dict):
            error_message = error_data.get('detail') or \
                            (error_data.get('non_field_errors')[0] if error_data.get('non_field_errors') else None) or \
                            "Nom d'utilisateur ou mot de passe invalide, ou erreur de connexion à l'API."
        else:
            error_message = "Erreur de connexion inattendue."

        QMessageBox.critical(self, "Échec de la Connexion", error_message)

    def show_login(self):
        """
        Méthode appelée par MainWindow.logout() pour revenir à cette fenêtre.
        """
        self.password_input.clear()
        self.username_input.clear()
        self.show()