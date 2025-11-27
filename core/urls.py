"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 1. Panel de Administración (REQ05)
    path('admin/', admin.site.urls),
    
    # 2. Rutas de la API REST (Backend) - REQ09
    # Todas las URLs de la API empiezan con /api/books/
    path('api/books/', include('books.urls')),
    
    # 3. Rutas del Sitio Web (Frontend) - REQ03
    # Usamos la cadena vacía '' para que atienda en la raíz (http://localhost:8000/)
    # Es importante que esto vaya al final para no ocultar otras rutas.
    path('', include('eco.urls')),
]