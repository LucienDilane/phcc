# medical_data/api/urls.py

from rest_framework.routers import DefaultRouter
from django.urls import path, include

# 🚨 Assurez-vous d'importer les ViewSets depuis l'emplacement où ils se trouvent.
# Basé sur le code que vous avez fourni, ils sont dans 'users.api.views'.
# Si vous les avez déplacés dans medical_data/api/views.py, ajustez l'import.
from users.api.views import SuiviViewSet, RendezVousViewSet,PatientViewSet 

router = DefaultRouter()
# 🚨 Enregistrement des ViewSets sous les chemins d'accès utilisés par l'API client
router.register(r'suivis', SuiviViewSet, basename='suivi')
router.register(r'rendezvous', RendezVousViewSet, basename='rendezvous')
router.register(r'patients', PatientViewSet, basename='patient')

urlpatterns = router.urls