
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, CustomAuthToken, SuiviViewSet, RendezVousViewSet, GlobalStatsView 

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
#router.register(r'suivis', SuiviViewSet)
router.register(r'rendezvous', RendezVousViewSet,basename='rendez-vous')
router.register(r'suivis', SuiviViewSet, basename='suivis')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', CustomAuthToken.as_view(), name='api_login'),
    path('stats/global/', GlobalStatsView.as_view(), name='stats-global'),
]