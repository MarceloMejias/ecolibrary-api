"""
Vistas de la API de Books.

Este módulo contiene todas las vistas para la gestión de libros,
incluyendo búsqueda externa en Google Books, registro de usuarios,
CRUD de libros y gestión de favoritos.
"""

from django.contrib.auth.models import User
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Favorite
from .serializers import BookSerializer, UserSerializer
from .services import search_google_books


class GoogleBooksSearchView(APIView):
    """
    Vista para buscar libros externamente usando la API de Google Books.
    
    Endpoint:
        GET /api/books/external-search/?q=termino
    
    Permisos:
        - AllowAny: Cualquier usuario (incluso anónimo) puede buscar libros externos.
    
    Query Parameters:
        q (str): Término de búsqueda. Es requerido.
    
    Responses:
        200: Lista de libros encontrados en Google Books.
        400: Error si el parámetro 'q' no fue proporcionado.
    
    Example:
        GET /api/books/external-search/?q=python%20programming
    """
    
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Maneja solicitudes GET para buscar libros en Google Books.
        
        Args:
            request: Objeto de solicitud HTTP con query parameters.
        
        Returns:
            Response: JSON con resultados de búsqueda o mensaje de error.
        """
        query = request.query_params.get('q', '')
        
        if not query:
            return Response(
                {"error": "Parámetro 'q' requerido"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = search_google_books(query)
        return Response(results, status=status.HTTP_200_OK)


class RegisterView(generics.CreateAPIView):
    """
    Vista pública para registrar nuevos usuarios en el sistema.
    
    Endpoint:
        POST /api/books/register/
    
    Permisos:
        - AllowAny: Cualquier persona puede crear una cuenta (Visitante).
    
    Request Body:
        {
            "username": "string",
            "email": "string",
            "password": "string"
        }
    
    Responses:
        201: Usuario creado exitosamente.
        400: Error de validación en los datos proporcionados.
    
    Example:
        POST /api/books/register/
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password123"
        }
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestionar el catálogo de libros internos.
    
    Provee operaciones CRUD completas para libros, además de funcionalidad
    para gestionar favoritos de usuarios autenticados.
    
    Endpoints:
        GET    /api/books/                      - Listar todos los libros
        GET    /api/books/{id}/                 - Detalle de un libro específico
        POST   /api/books/                      - Crear nuevo libro (solo Admin)
        PUT    /api/books/{id}/                 - Actualizar libro completo (solo Admin)
        PATCH  /api/books/{id}/                 - Actualizar parcialmente (solo Admin)
        DELETE /api/books/{id}/                 - Eliminar libro (solo Admin)
        GET    /api/books/my_favorites/         - Listar mis libros favoritos
        POST   /api/books/{id}/toggle_favorite/ - Agregar/Quitar de favoritos
    
    Permisos:
        - Lectura (GET): AllowAny - Cualquier usuario puede ver el catálogo.
        - Escritura (POST/PUT/PATCH/DELETE): IsAdminUser - Solo administradores.
        - Favoritos: IsAuthenticated - Solo usuarios autenticados.
    
    Reglas de Negocio:
        - REQ03: El catálogo es público para consulta.
        - REQ05, REQ09: Solo administradores pueden modificar el catálogo.
        - REQ06: Usuarios pueden agregar libros a favoritos.
        - REQ07: Usuarios pueden quitar libros de favoritos.
        - REQ08: Usuarios pueden listar sus libros favoritos.
        - RN02: Un usuario no puede duplicar un libro en favoritos.
    """
    
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        """
        Define permisos dinámicos según la acción HTTP realizada.
        
        Las acciones de lectura (list, retrieve) son públicas, mientras que
        las acciones de escritura (create, update, destroy) requieren permisos
        de administrador.
        
        Returns:
            list: Lista de instancias de clases de permisos aplicables.
        """
        if self.action in ['list', 'retrieve']:
            # REQ03: Cualquier usuario puede ver el catálogo
            permission_classes = [permissions.AllowAny]
        elif self.action in ['my_favorites', 'toggle_favorite']:
            # REQ06, REQ07, REQ08: Solo usuarios autenticados gestionan favoritos
            permission_classes = [IsAuthenticated]
        else:
            # REQ05 y REQ09: Solo administradores modifican el catálogo
            permission_classes = [permissions.IsAdminUser]
            
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_favorites(self, request):
        """
        Lista todos los libros marcados como favoritos por el usuario actual.
        
        Endpoint:
            GET /api/books/my_favorites/
        
        Permisos:
            - IsAuthenticated: Solo usuarios autenticados pueden ver sus favoritos.
        
        Args:
            request: Objeto de solicitud HTTP con usuario autenticado.
        
        Returns:
            Response: JSON con lista de libros favoritos del usuario.
        
        Reglas de Negocio:
            - REQ08: Listar favoritos del usuario autenticado.
            - RN02: Solo se listan favoritos únicos del usuario.
        
        Example Response:
            [
                {
                    "id": 1,
                    "title": "Python Programming",
                    "author": "John Doe",
                    ...
                }
            ]
        """
        user_favorites = Favorite.objects.filter(
            user=request.user
        ).values_list('book', flat=True)
        
        books = Book.objects.filter(id__in=user_favorites)
        serializer = self.get_serializer(books, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def toggle_favorite(self, request, pk=None):
        """
        Agrega o elimina un libro de la lista de favoritos (operación toggle).
        
        Si el libro ya está en favoritos, lo elimina. Si no está, lo agrega.
        Esta es una operación idempotente que facilita la gestión de favoritos
        desde el frontend.
        
        Endpoint:
            POST /api/books/{id}/toggle_favorite/
        
        Permisos:
            - IsAuthenticated: Solo usuarios autenticados pueden gestionar favoritos.
        
        Args:
            request: Objeto de solicitud HTTP con usuario autenticado.
            pk (int): ID del libro a agregar/quitar de favoritos.
        
        Returns:
            Response: JSON con el estado de la operación.
                - status: "added" si se agregó, "removed" si se eliminó.
                - message: Descripción de la acción realizada.
        
        Reglas de Negocio:
            - REQ06: Usuarios pueden agregar libros a favoritos.
            - REQ07: Usuarios pueden quitar libros de favoritos.
            - RN02: No se permiten duplicados (garantizado por unique_together).
        
        Example Response (agregado):
            {
                "status": "added",
                "message": "Libro agregado a favoritos"
            }
        
        Example Response (eliminado):
            {
                "status": "removed",
                "message": "Libro eliminado de favoritos"
            }
        """
        book = self.get_object()
        favorite_item, created = Favorite.objects.get_or_create(
            user=request.user,
            book=book
        )
        
        if not created:
            # Ya existía en favoritos, lo eliminamos (REQ07)
            favorite_item.delete()
            return Response(
                {
                    "status": "removed",
                    "message": "Libro eliminado de favoritos"
                },
                status=status.HTTP_200_OK
            )
        
        # Se creó nuevo favorito (REQ06)
        return Response(
            {
                "status": "added",
                "message": "Libro agregado a favoritos"
            },
            status=status.HTTP_201_CREATED
        )

