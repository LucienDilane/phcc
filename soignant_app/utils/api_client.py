# desktop_app/utils/api_client.py (Intégral)

import requests
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ApiClient:
    """
    Client HTTP personnalisé pour communiquer avec l'API Django REST Framework.
    """
    def __init__(self, base_url="http://127.0.0.1:8000/", token=None):
        self.base_url = base_url 
        
        self.session = requests.Session()
        self.token = token
        self.user_data = None

        if self.token:
            # 🚨 CORRECTION 1 : Utilisez 'Token' et self.token dans les headers de session 🚨
            self.session.headers.update({'Authorization': f'Token {self.token}'})

    def set_token(self, token):
        """Met à jour le token d'authentification et les headers de session."""
        self.token = token
        if self.token:
            self.session.headers.update({'Authorization': f'Token {self.token}'})

    def _get_auth_headers(self, is_json=False):
        # 🚨 VÉRIFIEZ L'EXISTENCE ET LA VALEUR DE self.token 🚨
        if not hasattr(self, 'token') or not self.token: 
            return {} 

        headers = {
            # 🚨 CORRECTION FINALE : Utiliser 'Token' et self.token 🚨
            'Authorization': f'Token {self.token}' # Ligne 380 (ou similaire) corrigée
        }
        if is_json:
            headers['Content-Type'] = 'application/json'
        return headers
    # --- Méthodes d'Authentification ---

    def login(self, username, password):
        """Tente de se connecter à l'API et de récupérer un Token."""
        url = f"{self.base_url}/api/v1/auth/login/"
        payload = {'username': username, 'password': password}
        
        try:
            response = self.session.post(url, data=payload)
            response.raise_for_status()

            data = response.json()
            self.user_data = data
            self.token = data.get('token')
            self.session.headers.update({'Authorization': f"Token {self.token}"})
            
            return data

        except requests.exceptions.HTTPError as e:
            if response.status_code in [400, 401]:
                return response.json()
            return {"error": f"Erreur HTTP: {response.status_code}", "details": str(e)}

        except requests.exceptions.RequestException as e:
            return {"error": "Erreur de connexion API.", "details": str(e)}

    def logout(self):
        """Nettoie la session en cas de déconnexion."""
        self.token = None
        self.user_data = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']


    # ⚠️ Méthode get_existing_usernames_by_prefix retirée.


    # --- Méthodes de Gestion des Patients ---

    def get_patients(self, search_term=""):
        """Récupère la liste des patients."""
        params = {'search': search_term} if search_term else {}
        url = f"{self.base_url}/api/v1/patients/"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                error_message = "Accès refusé. Vérifiez votre connexion."
            else:
                try:
                    error_json = response.json()
                    error_message = error_json.get('detail', f"Erreur {response.status_code}: Échec de la récupération des patients.")
                except json.JSONDecodeError:
                    error_message = f"Erreur HTTP {response.status_code}: {response.reason}"
            
            return {"error": error_message, "details": str(e)}

        except requests.exceptions.RequestException as e:
            return {"error": "Erreur de connexion API.", "details": str(e)}
    def _make_request(self, method, endpoint, data=None):
        """Méthode utilitaire pour exécuter une requête HTTP et gérer la réponse."""
        url = f"{self.base_url}api/v1/{endpoint}" 
        
        try:
            # Sérialiser les données en JSON
            json_data = json.dumps(data) if data is not None else None
            
            # Définir les headers pour les données JSON
            headers = self._get_auth_headers(is_json=True)
            
            # Exécution de la requête
            response = self.session.request(method, url, data=json_data, headers=headers)
            
            # Gérer les codes d'erreur HTTP (4xx ou 5xx)
            if response.status_code >= 400:
                # Retourne False, le code d'état et le corps JSON de l'erreur
                try:
                    error_details = response.json()
                except requests.JSONDecodeError:
                    error_details = response.text # Retourne le texte si pas JSON
                
                # 🚨 Retourne 3 valeurs pour gérer l'unpacking côté Qt
                return False, response.status_code, error_details

            # Succès (2xx)
            response.raise_for_status() # Lève une exception pour les autres erreurs 4xx/5xx non gérées ci-dessus
            
            # Si la réponse est 204 No Content (ex: DELETE), ne pas essayer de lire le JSON
            if response.status_code == 204:
                 # 🚨 Retourne 3 valeurs pour gérer l'unpacking côté Qt
                return True, response.status_code, {} 

            # Retourne True, la réponse JSON et un code d'état
            return True, response.status_code, response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête à {url}: {e}")
             # 🚨 Retourne 3 valeurs en cas d'erreur réseau
            return False, 0, {"network_error": str(e)}

    # ------------------------------------------------------------------
    # Méthodes spécifiques au Patient
    # ------------------------------------------------------------------
    
    def create_patient(self, payload):
        """Crée un nouveau patient via l'API (POST)."""
        endpoint = f"{self.base_url}api/v1/patients/" 
        headers = self._get_auth_headers(is_json=True)

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
            
            # Succès (201 Created)
            return True, response.json() 

        except requests.exceptions.RequestException as e:
            # Échec
            error_details = self._extract_error_message(e)
            return False, {'error': error_details}
            
    def update_patient(self, patient_id, payload):
        """Met à jour un patient existant via l'API (PUT/PATCH)."""
        # On utilise PATCH pour n'envoyer que les champs modifiés (plus efficace)
        endpoint = f"{self.base_url}api/v1/patients/{patient_id}/" 
        headers = self._get_auth_headers(is_json=True)

        try:
            # NOTE: Nous utilisons PATCH pour une mise à jour partielle
            response = requests.patch(endpoint, headers=headers, json=payload)
            response.raise_for_status() 
            
            # Succès (200 OK)
            return True, response.json() 

        except requests.exceptions.RequestException as e:
            # Échec
            error_details = self._extract_error_message(e)
            return False, {'error': error_details}


    def delete_patient(self, patient_id):
        """Envoie une requête DELETE pour supprimer un patient."""
        url = f"{self.base_url}/api/v1/patients/{patient_id}/"
        
        try:
            response = self.session.delete(url) 
            response.raise_for_status() 

            return True

        except requests.exceptions.HTTPError as e:
            return {"error": f"Erreur de suppression: {response.status_code}", "details": str(e)}

        except requests.exceptions.RequestException as e:
            return {"error": "Erreur de connexion API.", "details": str(e)}
    
    #------Suivie et plans------#
    def get_follow_ups(self, patient_id):
        endpoint = f"{self.base_url}api/suivis/"
        params = {'patient_id': patient_id} 
        
        try:
            response = requests.get(endpoint, headers=self._get_auth_headers(), params=params)
            response.raise_for_status() # Ceci lève l'exception pour les codes 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            # 🚨 Ajout du code d'erreur dans le message
            status_code = http_err.response.status_code
            error_detail = f"Erreur {status_code}: {http_err.response.text[:100]}..." 
            return {'error': f"Échec du chargement des suivis: {error_detail}"}
        except requests.RequestException as e:
            return {'error': f"Échec du chargement des suivis: Erreur réseau/connexion - {e}"}
        
    def create_follow_up(self, data):
        """
        Crée un nouveau suivi pour un patient.
        Endpoint: POST /api/suivis/
        """
        endpoint = f"{self.base_url}api/suivis/"
        try:
            response = requests.post(endpoint, headers=self._get_auth_headers(), json=data)
            response.raise_for_status() 
            
            return True, response.json()
        
        # Gère les erreurs HTTP (4xx, 5xx), PAS les erreurs de connexion
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            try:
                error_data = http_err.response.json()
            except json.JSONDecodeError:
                error_data = {'detail': f"Erreur {status_code}: Réponse non JSON ou vide."}
            
            return False, {'error': f"Échec HTTP {status_code}: {error_data.get('detail', error_data)}"}
            
        # 🚨 C'est ce bloc qui est exécuté lorsque vous voyez l'erreur
        except requests.RequestException as e:
            # Cette erreur est générée lorsque la connexion TCP ne peut pas être établie.
            return False, {'error': f"Échec de la connexion au réseau lors de l'enregistrement: {e}"}

    ## Gestion des Rendez-vous---------

    def get_rendez_vous(self, patient_id=None):
        """
        Récupère tous les rendez-vous ou ceux d'un patient spécifique en utilisant
        le paramètre de requête 'patient_id'.
        Endpoint: GET /api/rendezvous/ ou GET /api/rendezvous/?patient_id=X
        """
        endpoint = f"{self.base_url}api/rendezvous/"
        params = {}
        
        # 🚨 Étape cruciale : Ajouter le patient_id aux paramètres de la requête GET
        if patient_id is not None:
            params['patient_id'] = patient_id 

        try:
            # Envoi de la requête GET avec les paramètres (params=params)
            response = requests.get(endpoint, headers=self._get_auth_headers(), params=params)
            response.raise_for_status() 
            return response.json()
        
        except requests.RequestException as e:
            # Gérer les erreurs HTTP (4xx/5xx) ou de connexion
            error_message = f"Échec de connexion réseau/API lors du chargement des RDV: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Erreur HTTP {e.response.status_code}: {error_data.get('detail', error_data)}"
                except json.JSONDecodeError:
                    error_message = f"Erreur HTTP {e.response.status_code}: Réponse non JSON."
                    
            return {'error': error_message}


    def create_rendez_vous(self, data):
        """
        Crée un nouveau rendez-vous via l'API (POST).
        Endpoint: POST /api/rendezvous/
        """
        endpoint = f"{self.base_url}api/rendezvous/"
        try:
            # Envoi des données JSON
            response = requests.post(endpoint, headers=self._get_auth_headers(), json=data)
            response.raise_for_status() # Lève une exception pour les codes d'erreur 4xx/5xx
            
            # Un POST réussi retourne souvent 201 Created
            return True, response.json()
            
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            try:
                # Tente de décoder les erreurs JSON du backend
                error_data = http_err.response.json()
            except json.JSONDecodeError:
                error_data = {'detail': f"Erreur {status_code}: Réponse non JSON ou vide."}
                
            return False, {'error': f"Échec HTTP {status_code}: {error_data.get('detail', error_data)}"}
            
        except requests.RequestException as e:
            return False, {'error': f"Échec de connexion réseau lors de la création du RDV: {e}"}

    def update_rendez_vous(self, rdv_id, data):
        """
        Modifie un rendez-vous existant via l'API (PATCH/PUT). 
        Utiliser PATCH pour la modification partielle.
        Endpoint: PATCH /api/rendezvous/{id}/
        """
        endpoint = f"{self.base_url}api/rendezvous/{rdv_id}/"
        try:
            # Utilisation de PATCH pour mettre à jour partiellement
            response = requests.patch(endpoint, headers=self._get_auth_headers(), json=data)
            response.raise_for_status() 
            
            return True, response.json()
            
        except requests.RequestException as e:
            # ... (Gestion des erreurs similaire à create_rendez_vous) ...
            error_message = f"Échec de connexion réseau lors de la mise à jour du RDV: {e}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"Erreur HTTP {e.response.status_code}: {error_data.get('detail', error_data)}"
                except json.JSONDecodeError:
                    error_message = f"Erreur HTTP {e.response.status_code}: Réponse non JSON."
                    
            return False, {'error': error_message}

    def delete_rendez_vous(self, rdv_id):
        """
        Supprime un rendez-vous.
        Endpoint: DELETE /api/rendezvous/{id}/
        """
        endpoint = f"{self.base_url}api/rendezvous/{rdv_id}/"
        try:
            response = requests.delete(endpoint, headers=self._get_auth_headers())
            response.raise_for_status() # Un DELETE réussi renvoie souvent 204 No Content
            return True, {}
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            return False, {'error': f"Échec HTTP {status_code}: Impossible de supprimer le RDV."}
        except requests.RequestException as e:
            return False, {'error': f"Échec de connexion réseau lors de la suppression du RDV: {e}"}
    

    def search_patients(self, query):
        """Recherche des patients via l'API par terme de recherche (nom, prénom, identifiant)."""
        # 🚨 Vous devez vous assurer que votre API Django gère le paramètre ?search= 🚨
        endpoint = f"{self.base_url}api/patients/?search={query}"
        
        try:
            response = requests.get(endpoint, headers=self._get_auth_headers())
            response.raise_for_status()
            response_data=response.json()

            # Si la réponse est un dictionnaire (comme dans la pagination), les données sont dans 'results'.
            if isinstance(response_data, dict) and 'results' in response_data:
                patients = response_data['results']
            else:
                # Sinon, la réponse est une liste directe ou une réponse vide
                patients = response_data if isinstance(response_data, list) else []
            
            return True, patients 
            
        except requests.exceptions.RequestException as e:
            error_message = self._extract_error_message(e)
            return False, {'error': error_message}
            
        except json.JSONDecodeError:
            # Gère explicitement le cas où le JSON est vide ou mal formé (statut 200, mais corps vide)
            return False, {'error': "Erreur de décodage JSON : La réponse est vide ou invalide."}
            
    # Cette méthode est nécessaire si vous ne l'avez pas déjà :
    def _extract_error_message(self, e):
        """Extrait le message d'erreur d'une exception de requête."""
        error_message = f"Échec de connexion réseau: {e}"
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            try:
                error_data = e.response.json()
                detail = error_data.get('detail', error_data)
                error_message = f"Erreur HTTP {status_code}: {detail}"
            except:
                error_message = f"Erreur HTTP {status_code}: Réponse non JSON ou vide."
        return error_message
    
    def patch_rendez_vous(self, rdv_id: int, update_data: dict):
        """Met à jour partiellement les données d'un rendez-vous (ex: statut)."""
        endpoint = f"{self.base_url}api/rendezvous/{rdv_id}/"
        
        try:
            response = requests.patch(
                endpoint, 
                headers=self._get_auth_headers(is_json=True), # Assurez-vous que le content-type est JSON
                json=update_data
            )
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.RequestException as e:
            error_message = self._extract_error_message(e)
            return False, {'error': error_message}
    

    def get_suivis(self, patient_id=None):
        """Récupère la liste des Suivis, filtrée par patient."""
        endpoint = f"{self.base_url}api/suivis/"
        params = {}
        if patient_id:
            params['patient'] = patient_id # Envoie ?patient=X
            
        try:
            response = requests.get(endpoint, headers=self._get_auth_headers(), params=params)
            response.raise_for_status()
            
            response_data = response.json()
            
            # 🚨 CORRECTION : Définir 'items' en fonction du format de réponse 🚨
            # Vérifie si c'est une réponse paginée (dictionnaire avec clé 'results')
            if isinstance(response_data, dict) and 'results' in response_data:
                items = response_data['results']
            # Vérifie si c'est une liste directe
            elif isinstance(response_data, list):
                items = response_data
            else:
                # Si le format est inconnu (ex: dictionnaire vide), retourne une liste vide
                items = []
            
            return True, items 
            
        except requests.exceptions.RequestException as e:
            error_message = self._extract_error_message(e)
            return False, {'error': error_message}
    
    def get_global_stats(self):
        """Récupère les statistiques agrégées globales."""
        # 🚨 CORRECTION : Ajout du préfixe 'v1/' pour correspondre au routage Django 🚨
        endpoint = f"{self.base_url}api/v1/stats/global/" 
        
        try:
            response = requests.get(endpoint, headers=self._get_auth_headers())
            response.raise_for_status()
            return True, response.json()
            
        except requests.exceptions.RequestException as e:
            error_message = self._extract_error_message(e)
            return False, {'error': error_message}
   