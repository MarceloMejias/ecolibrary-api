from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import BookViewSet, OpenLibrarySearchView

router = DefaultRouter()
router.register(r'local', BookViewSet, basename='local-book')

urlpatterns = [
    path('', include(router.urls)),
    path('external-search/', OpenLibrarySearchView.as_view(), name='external-search'),
    path('login/', obtain_auth_token, name='api_token_auth'),
]