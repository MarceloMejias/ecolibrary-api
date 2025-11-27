from django.urls import path

from . import views

urlpatterns = [
    # Ruta principal
    path('', views.index, name='index'),

    # Rutas de autenticación
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Rutas de Libros
    path('book/<int:book_id>/', views.book_detail, name='book_detail'), # REQ03
    path('favorites/', views.favorites_view, name='favorites'),         # REQ08
path('book/<int:book_id>/favorite/', views.toggle_favorite_web, name='toggle_favorite'),]