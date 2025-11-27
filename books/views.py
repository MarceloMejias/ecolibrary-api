from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Favorite
from .serializers import BookSerializer, EmptySerializer
from .services import search_open_library

# API REST

class OpenLibrarySearchView(APIView):
    """Vista API para buscar libros externamente (Open Library)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({"error": "Parámetro 'q' requerido"}, status=status.HTTP_400_BAD_REQUEST)
        results = search_open_library(query)
        return Response(results, status=status.HTTP_200_OK)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_favorites(self, request):
        user_favorites = Favorite.objects.filter(user=request.user).values_list('book', flat=True)
        books = Book.objects.filter(id__in=user_favorites)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], serializer_class=EmptySerializer)
    def toggle_favorite(self, request, pk=None):
        book = self.get_object()
        favorite_item, created = Favorite.objects.get_or_create(user=request.user, book=book)
        if not created:
            favorite_item.delete()
            return Response({"status": "removed", "message": "Eliminado de favoritos"}, status=200)
        return Response({"status": "added", "message": "Agregado a favoritos"}, status=201)