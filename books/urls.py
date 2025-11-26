from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token # Vista nativa de login
from .views import BookViewSet, GoogleBooksSearchView, RegisterView

router = DefaultRouter()
router.register(r'local', BookViewSet, basename='local-book')

urlpatterns = [
    path('', include(router.urls)),
    path('external-search/', GoogleBooksSearchView.as_view(), name='external-search'),
    
    # Rutas de Autenticación
    path('register/', RegisterView.as_view(), name='register'), # REQ01
    path('login/', obtain_auth_token, name='api_token_auth'),   # REQ02 (Devuelve el Token)
]