# main_app.py (Nouveau Fichier ou votre ancien app.py renommé)
import sys
from PyQt6.QtWidgets import QApplication
from .login_window import LoginWindow # Assurez-vous d'avoir toujours la LoginWindow
from .utils.api_client import ApiClient

def start_application():
    app = QApplication(sys.argv)
    
    # 🚨 Assure l'arrêt du programme quand la dernière fenêtre est fermée
    app.setQuitOnLastWindowClosed(True) 
    
    api_client = ApiClient(base_url="http://127.0.0.1:8000/")
    
    # Lancement de la fenêtre initiale
    login_window = LoginWindow(api_client)
    login_window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    start_application()