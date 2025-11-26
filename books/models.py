"""
Modelos de la aplicación Books.

Define los modelos Book y Favorite para el catálogo de libros
y la gestión de favoritos de usuarios.
"""

from django.contrib.auth.models import User
from django.db import models


class Book(models.Model):
    """
    Modelo que representa un libro en el catálogo.
    
    Attributes:
        title (str): Título del libro (requerido).
        author (str): Autor del libro (requerido).
        description (str): Descripción breve del contenido.
        category (str): Categoría o género literario.
        publication_year (int): Año de publicación.
        external_id (str): ID de APIs externas (Google Books, OpenLibrary).
        cover_url (str): URL de la imagen de portada.
        created_at (datetime): Fecha de creación del registro.
        updated_at (datetime): Fecha de última actualización.
    
    Business Rules:
        - REQ01, RN01: Información mínima obligatoria del libro.
    """
    
    # Información básica obligatoria
    title = models.CharField(max_length=255, verbose_name="Título")
    author = models.CharField(max_length=255, verbose_name="Autor")
    description = models.TextField(verbose_name="Descripción breve")
    category = models.CharField(max_length=100, verbose_name="Categoría")
    publication_year = models.PositiveIntegerField(verbose_name="Año de publicación")
    
    # Integración con APIs externas
    external_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID Externo (Google/OpenLib)"
    )
    cover_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="URL de Portada"
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Representación en string del libro."""
        return f"{self.title} ({self.publication_year})"

    class Meta:
        verbose_name = "Libro"
        verbose_name_plural = "Libros"
        ordering = ['-created_at']


class Favorite(models.Model):
    """
    Modelo que representa la relación entre usuarios y libros favoritos.
    
    Attributes:
        user (User): Usuario que marca el favorito.
        book (Book): Libro marcado como favorito.
        added_at (datetime): Fecha en que se agregó a favoritos.
    
    Business Rules:
        - RN02: Un usuario no puede marcar el mismo libro como favorito múltiples veces.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Usuario"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="Libro"
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha agregado")

    def __str__(self):
        """Representación en string del favorito."""
        # Safely access attributes in case static analysis can't infer ForeignKey types.
        username = getattr(self.user, "username", str(self.user))
        title = getattr(self.book, "title", str(self.book))
        return f"{username} - {title}"

    class Meta:
        verbose_name = "Favorito"
        verbose_name_plural = "Favoritos"
        unique_together = ('user', 'book')
        ordering = ['-added_at']