# desktop_app/login_widget.py
import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSignal

class LoginWidget(QWidget):
    
    # Signal pour envoyer le token à la fenêtre principale après succès
    login_successful = pyqtSignal(str) 

    def __init__(self, api_url, parent=None):
        super().__init__(parent)
        self.api_url = api_url
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Se Connecter")
        self.login_button.clicked.connect(self.attempt_login)
        
        layout.addWidget(QLabel("Connexion Soignant"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

    def attempt_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        login_url = f"{self.api_url}token/" # Assurez-vous que cette URL est correcte (ex: /api/token/)

        try:
            response = requests.post(login_url, data={'username': username, 'password': password})
            
            if response.status_code == 200:
                # Connexion réussie : le serveur a renvoyé le token
                token = response.json().get('token')
                if token:
                    # Émet le signal avec le token pour que la fenêtre principale soit lancée
                    self.login_successful.emit(token)
                else:
                    QMessageBox.warning(self, "Erreur d'API", "Réponse du serveur incomplète (token manquant).")
            elif response.status_code == 400:
                # Échec d'authentification (mauvais identifiants)
                QMessageBox.critical(self, "Échec de Connexion", "Nom d'utilisateur ou mot de passe incorrect.")
            elif response.status_code == 404:
                # Le point de terminaison n'existe pas
                QMessageBox.critical(self, "Erreur Serveur", "Le point de terminaison d'authentification est introuvable (404 Not Found).")
            else:
                # Autres erreurs serveur
                QMessageBox.critical(self, "Erreur Serveur", f"Erreur inattendue: {response.status_code} - {response.text[:100]}...")

        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Erreur de Connexion", "Impossible de se connecter au serveur Django. Assurez-vous qu'il est lancé.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur Inconnue", f"Une erreur s'est produite : {e}")