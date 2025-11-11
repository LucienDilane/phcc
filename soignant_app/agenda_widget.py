from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QCalendarWidget, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QHeaderView, QTableWidget, QInputDialog, QLineEdit, QMenu
)
from PyQt6.QtCore import Qt, QDate, QDateTime
from datetime import datetime
from .utils.api_client import ApiClient 
from .patient_folder_window import AddRendezVousDialog, RendezVousHistoryWidget
from .dialogs import PatientSearchDialog
# Supposons que ApiClient est importé comme suit
class AgendaAndPlansWidget(QWidget):
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Utilisation de QTabWidget pour séparer Agenda et Plans
        self.tabs = QTabWidget()
        
        # Onglet 1 : Agenda des Rendez-vous
        self.agenda_widget = AgendaWidget(self.api_client)
        self.tabs.addTab(self.agenda_widget, "🗓️ Agenda des Rendez-vous")
        
        # Onglet 2 : Plans de Soins
        self.plans_widget = SuiviHistoriqueWidget(self.api_client)
        self.tabs.addTab(self.plans_widget, "📝 Plans de Soins & Suivi")
        
        main_layout.addWidget(self.tabs)

            ###  AGENDA ###

class AgendaWidget(QWidget):
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_rdv_data = [] 
        self.init_ui()
        self.load_daily_appointments(QDate.currentDate())
        
    def init_ui(self):
        # 🚨 1. Définir le layout principal 🚨
        main_layout = QHBoxLayout(self) 

        # --- 2. Panneau Gauche : Calendrier ---
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setGridVisible(True)
        self.calendar.selectionChanged.connect(self._on_date_changed)
        
        # 🚨 Définir une taille fixe pour le calendrier 🚨
        # Ceci empêche le calendrier de prendre toute la place.
        # Ajustez ces valeurs (par exemple 350x300) selon vos préférences.
        self.calendar.setFixedWidth(350)
        self.calendar.setMaximumHeight(300) 

        # Ajouter le calendrier à gauche
        left_panel = QVBoxLayout()
        left_panel.addWidget(self.calendar)
        # Optionnel : Ajoutez ici des contrôles de filtre si vous en avez
        
        main_layout.addLayout(left_panel) # Ajouter le panneau gauche au layout principal

        # --- 3. Panneau Droit : Liste des RDV et Boutons ---
        right_panel = QVBoxLayout()
        self.rdv_list_label = QLabel("Rendez-vous pour la date sélectionnée")
        self.rdv_list_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 5px;")
        # Bouton Ajouter RDV
        self.add_rdv_button = QPushButton("➕ Planifier un nouveau RDV")
        self.add_rdv_button.clicked.connect(self.open_new_rdv_dialog)
        self.add_rdv_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        
        # Liste des RDV
        self.rdv_list_widget = QListWidget()
        self.rdv_list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rdv_list_widget.customContextMenuRequested.connect(self.show_rdv_context_menu)
        
        # Remplir le panneau de droite
        right_panel.addWidget(self.rdv_list_label)
        right_panel.addWidget(self.add_rdv_button)
        right_panel.addWidget(self.rdv_list_widget)
        
        # 🚨 4. Ajouter le panneau droit 🚨
        main_layout.addLayout(right_panel)
        
        # 🚨 5. Ajustement de l'étirement 🚨
        # Permettre au panneau droit de s'étirer pour prendre l'espace restant
        main_layout.setStretchFactor(right_panel, 1) 
        main_layout.setStretchFactor(left_panel, 0) # Le panneau gauche est fixe
    
    def _on_date_changed(self):
        """
        Gère le changement de date sélectionnée sur le calendrier.
        Charge les rendez-vous pour la nouvelle date.
        """
        selected_date = self.calendar.selectedDate()
        self.load_daily_appointments(selected_date)

    def load_daily_appointments(self, date: QDate):
        """Charge les RDV pour la date sélectionnée."""
        selected_date_str = date.toString("yyyy-MM-dd")
        self.rdv_list_label.setText(f"Rendez-vous pour le {date.toString('dd/MM/yyyy')}")
        self.rdv_list_widget.clear()
        
        # TODO: Adapter l'appel API pour filtrer par date
        # Nous allons simuler un filtre pour l'instant, car l'API Django doit être mise à jour
        
        # 🚨 SIMULATION : Vous devez implémenter cette méthode dans votre ApiClient 🚨
        # response = self.api_client.get_rendez_vous_by_date(selected_date_str)
        response = self.api_client.get_rendez_vous() # Charge tous les RDV pour la démo
        
        if isinstance(response, list):
            
            # Filtrer côté client pour les RDV du jour
            daily_rdvs = [
                rdv for rdv in response 
                if rdv.get('date_heure', '').startswith(selected_date_str)
            ]
            
            # Trier par heure
            daily_rdvs.sort(key=lambda x: x.get('date_heure'))
            self.current_rdv_data = daily_rdvs
            
            if not daily_rdvs:
                self.rdv_list_widget.addItem("Aucun rendez-vous planifié pour cette journée.")
                return

            for rdv in daily_rdvs:
                item_text = self._format_rdv_item(rdv)
                item = QListWidgetItem(item_text)
                self.rdv_list_widget.addItem(item)
        else:
            self.rdv_list_widget.addItem(f"Erreur de chargement: {response.get('error', 'API erreur')}")


    def _format_rdv_item(self, rdv: dict) -> str:
        """Formate l'affichage d'un RDV dans la liste avec le nom et le contact du patient."""
        try:
            dt = datetime.fromisoformat(rdv['date_heure'])
            time_str = dt.strftime("%H:%M")
        except:
            time_str = "N/A"
            
        statut_code = rdv.get('statut', 'P')
        
        # 🚨 MISE À JOUR : Récupérer le nom et le téléphone du patient 🚨
        
        # ⚠️ HYPOTHÈSE : L'API a été modifiée pour inclure ces clés.
        patient_name = rdv.get('patient_name', 'Patient inconnu')
        patient_phone = rdv.get('patient_phone', 'N/A')
        
        # Affichage du statut lisible (vous pouvez réutiliser la fonction _get_statut_display si vous l'avez)
        statut_display = ""
        if statut_code == 'P': statut_display = "Planifié"
        elif statut_code == 'C': statut_display = "Confirmé"
        elif statut_code == 'A': statut_display = "Annulé"
        elif statut_code == 'T': statut_display = "Terminé"
        else: statut_display = statut_code
        
        # Nouveau format d'affichage
        return (
            f"**{time_str}** - {patient_name} "
            f"(Tél: {patient_phone}) - Motif: {rdv.get('motif', 'N/A')} "
            f"[Statut: {statut_display}]"
        )
    # TODO: Ajouter open_rdv_details pour le double-clic

    def open_new_rdv_dialog(self):
        """
        Ouvre le dialogue de planification de RDV. 
        Nécessite de sélectionner un patient si l'on est dans la vue Agenda.
        """
        # 1. Ouverture du dialogue de recherche de patient
        search_dialog = PatientSearchDialog(api_client=self.api_client, parent=self)
        
        if search_dialog.exec() != QDialog.DialogCode.Accepted:
            QMessageBox.warning(self, "Action Annulée", "Sélection du patient annulée.")
            return

        patient_data = search_dialog.get_selected_patient()
        
        if not patient_data:
            QMessageBox.warning(self, "Erreur", "Aucun patient sélectionné.")
            return

        # 2. Déterminer la date par défaut
        selected_date = self.calendar.selectedDate()
        
        # Créer un QDateTime pour le début de la prochaine heure pour le dialogue
        default_datetime = QDateTime(selected_date, self._get_next_hour_time()) 
        
        # 3. Ouvrir le dialogue de création de RDV
        # Remarque : La classe AddRendezVousDialog doit être disponible ici
        # Si AddRendezVousDialog est dans patient_folder_window.py, assurez-vous qu'elle est importée.
        dialog = AddRendezVousDialog(
            api_client=self.api_client, 
            patient_data=patient_data, 
            default_datetime=default_datetime, # Argument optionnel à gérer dans __init__ de AddRendezVousDialog
            existing_rdv_data=None, 
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Succès", "Rendez-vous planifié avec succès.")
            # Recharger les RDV pour la date actuelle
            self.load_daily_appointments(self.calendar.selectedDate())
            
    def _get_next_hour_time(self):
        """Retourne l'heure complète suivante (ex: 16:00 si l'heure actuelle est 15:30)."""
        now = QDateTime.currentDateTime()
        return now.addSecs(3600 - (now.time().minute() * 60 + now.time().second())).time()
    
    
    def _select_patient_for_rdv(self):
        """
        Simule la sélection d'un patient pour un nouveau RDV. 
        Dans une vraie app, cela ouvrirait un dialogue de recherche de patient.
        Nous allons simuler ici avec un QInputDialog pour le Patient ID.
        """
        patient_id, ok = QInputDialog.getText(
            self, 
            'Sélectionner Patient', 
            'Entrez l\'ID du patient (pour la démonstration):', 
            QLineEdit.EchoMode.Normal, 
            ""
        )
        
        if ok and patient_id:
            try:
                # 🚨 Simulation : Vous devrez appeler une vraie API pour valider l'ID et obtenir les détails 🚨
                # Pour l'instant, nous renvoyons un dictionnaire minimal avec l'ID pour que AddRendezVousDialog fonctionne.
                return {'id': int(patient_id), 'first_name': f'Patient #{patient_id}', 'last_name': ''}
            except ValueError:
                QMessageBox.critical(self, "Erreur", "L'ID du patient doit être un nombre valide.")
                return None
        return None


    def _get_selected_rdv_data(self) -> dict | None:
        """Récupère les données complètes du RDV sélectionné."""
        selected_item = self.rdv_list_widget.currentItem()
        if not selected_item:
            return None
        
        # L'index de l'élément sélectionné dans la QListWidget
        row = self.rdv_list_widget.row(selected_item)
        
        # Nous avions stocké les données des RDV chargés pour le jour
        if 0 <= row < len(self.current_rdv_data):
            return self.current_rdv_data[row]
        
        return None

    def show_rdv_context_menu(self, pos):
        """Affiche le menu contextuel lors du clic droit sur un RDV."""
        rdv_data = self._get_selected_rdv_data()
        if not rdv_data:
            return

        context_menu = QMenu(self)
        
        # 1. Action Modifier
        edit_action = context_menu.addAction("✏️ Modifier le RDV") 
        context_menu.addSeparator()

        # 2. Actions de Statut (Dépendent du statut actuel)
        statut = rdv_data.get('statut')

        if statut == 'P' or statut == 'C': # Planifié ou Confirmé
            complete_action = context_menu.addAction("✅ Marquer comme Terminé")
            cancel_action = context_menu.addAction("❌ Annuler le RDV")
        else: # Terminé ('T') ou Annulé ('A')
            # Permettre de remettre en Planifié (si erreur)
            replan_action = context_menu.addAction("🔁 Remettre en Planifié")
        
        # Afficher le menu à la position du clic
        action = context_menu.exec(self.rdv_list_widget.mapToGlobal(pos))

        # Gérer les actions
        if action == edit_action:
            self.open_edit_rdv_dialog(rdv_data)
        elif action == complete_action:
            self.update_rdv_status(rdv_data, 'T', "Terminé")
        elif action == cancel_action:
            self.confirm_cancel_rdv(rdv_data)
        elif action == replan_action:
            self.update_rdv_status(rdv_data, 'P', "Planifié")

    def open_edit_rdv_dialog(self, rdv_data: dict):
        """Ouvre le dialogue de modification pour un RDV existant."""
        
        # NOTE: Vous devez vous assurer que la classe AddRendezVousDialog est importée.
        # Nous devons aussi passer les données complètes du patient.
        # Pour l'agenda, nous utilisons un dictionnaire patient minimal, car nous n'avons que l'ID par défaut
        # Dans le contexte de l'agenda, nous ne récupérons que l'ID du patient. 
        patient_data_minimal = {'id': rdv_data.get('patient')} 
        
        # Le dialogue s'ouvrira en mode édition car existing_rdv_data est fourni.
        dialog = AddRendezVousDialog(
            api_client=self.api_client, 
            patient_data=patient_data_minimal, 
            existing_rdv_data=rdv_data, 
            default_datetime=None, 
            parent=self
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            QMessageBox.information(self, "Succès", "Rendez-vous modifié avec succès.")
            # Recharger les RDV pour la date actuelle
            self.load_daily_appointments(self.calendar.selectedDate())


    def update_rdv_status(self, rdv_data: dict, new_status: str, status_label: str):
        """Met à jour le statut d'un RDV via l'API."""
        rdv_id = rdv_data.get('id')
        if not rdv_id:
            QMessageBox.critical(self, "Erreur", "ID du rendez-vous manquant.")
            return

        # Appel API pour mettre à jour le statut
        # 🚨 Vous devez ajouter une méthode patch_rendez_vous à votre ApiClient 🚨
        success, response = self.api_client.patch_rendez_vous(
            rdv_id=rdv_id, 
            update_data={'statut': new_status}
        )
        
        if success:
            QMessageBox.information(self, "Succès", f"Rendez-vous marqué comme {status_label} avec succès.")
            self.load_daily_appointments(self.calendar.selectedDate())
        else:
            details = response.get('error', 'Détails non disponibles.')
            QMessageBox.critical(self, "Erreur API", f"Échec de la mise à jour du statut.\n\nErreur : {details}")


    def confirm_cancel_rdv(self, rdv_data: dict):
        """Demande confirmation avant d'annuler le RDV."""
        reply = QMessageBox.question(
            self, 
            "Confirmer Annulation",
            f"Êtes-vous sûr de vouloir annuler le rendez-vous de {rdv_data.get('patient_name', 'ce patient')} à {datetime.fromisoformat(rdv_data['date_heure']).strftime('%H:%M')} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.update_rdv_status(rdv_data, 'A', "Annulé")
            ### PLANS ###


class SuiviHistoriqueWidget(QWidget): # Renommage pour plus de clarté
    """Widget affichant la chronologie des Suivis (incluant les plans de soin) d'un patient."""
    def __init__(self, api_client, patient_data=None, parent=None): 
        super().__init__(parent)
        self.api_client = api_client
        self.patient_data = patient_data # Peut être None
        self.suivis_data = [] 
        self.init_ui()
        self.load_suivis()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Le titre dépendra de si nous sommes en vue globale ou patient
        if self.patient_data:
            title = f"Historique de Suivi pour : {self.patient_data.get('last_name')}"
        else:
            title = "Aperçu des Derniers Suivis / Plans Globaux"
            
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        main_layout.addWidget(self.title_label)
        
        self.suivis_list = QListWidget() # Renommage de plans_list
        main_layout.addWidget(self.suivis_list)
        
        # Bouton d'action (Ajouter un nouveau suivi/plan)
        self.add_btn = QPushButton("➕ Ajouter un nouveau Suivi/Plan")
        # Le clic devra ouvrir AddFollowUpDialog (si vous l'avez)
        # self.add_btn.clicked.connect(self.open_add_suivi_dialog) 
        
        main_layout.addWidget(self.add_btn)


    def load_suivis(self):
        """Charge l'historique de suivi (patient spécifique ou global)."""
        patient_id = self.patient_data.get('id') if self.patient_data else None
        
        # Si patient_id est None, get_suivis chargera l'historique global
        success, suivis = self.api_client.get_suivis(patient_id=patient_id)

        if success:
            self.suivis_data = suivis
            for suivi in suivis:
                # Affichage des informations clés du suivi/plan
                date_str = datetime.fromisoformat(suivi.get('date_suivi')).strftime('%d/%m/%Y %H:%M')
                motif = suivi.get('motif', 'N/A')
                notes = suivi.get('notes_medecin', 'Aucune note.')
                
                # Mise en forme de l'item
                display_text = (
                    f"[{date_str}] - Motif: {motif}\n"
                    f"Plan/Notes: {notes[:100]}..." # Afficher le début des notes
                )
                item = QListWidgetItem(display_text)
                
                item.setData(Qt.ItemDataRole.UserRole, suivi) # Stocker les données complètes
                self.suivis_list.addItem(item)
        else:
            QMessageBox.critical(self, "Erreur API", "Échec du chargement de l'historique de suivi.")