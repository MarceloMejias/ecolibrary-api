from django.contrib import admin, messages
from rest_framework.authtoken.models import TokenProxy

from .models import Book, Favorite

# Ocultar los tokens de autenticación del admin
admin.site.unregister(TokenProxy)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'publication_year', 'has_cover', 'favorites_count')
    search_fields = ('title', 'author', 'external_id')
    list_filter = ('category', 'publication_year')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Identificador (Auto-relleno)', {
            'fields': ('external_id',),
            'description': 'Ingresa el ID de Open Library (ej: OL123456W) y los demás campos se rellenarán automáticamente al guardar.'
        }),
        ('Información Básica', {
            'fields': ('title', 'author', 'description', 'category', 'publication_year')
        }),
        ('Portada', {
            'fields': ('cover_url',),
            'description': 'Opcional: deja vacío para obtener automáticamente desde Open Library.'
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['fetch_data_from_openlibrary']
    
    def has_cover(self, obj):
        """Indica si el libro tiene portada."""
        return bool(obj.get_cover_url())
    has_cover.boolean = True
    has_cover.short_description = 'Portada'
    
    def favorites_count(self, obj):
        """Muestra cuántos usuarios tienen este libro como favorito."""
        return obj.favorited_by.count()
    favorites_count.short_description = '❤️ Favoritos'
    favorites_count.admin_order_field = 'favorited_by__count'
    
    def fetch_data_from_openlibrary(self, request, queryset):
        """Acción para actualizar datos desde Open Library."""
        updated = 0
        for book in queryset:
            if book.fetch_book_data_from_openlibrary():
                book.save()
                updated += 1
        
        self.message_user(
            request,
            f'{updated} libro(s) actualizado(s) desde Open Library.',
            messages.SUCCESS
        )
    fetch_data_from_openlibrary.short_description = "Actualizar desde Open Library"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'book_title', 'book_author', 'added_at')
    list_filter = ('added_at', 'user')
    search_fields = ('user__username', 'book__title', 'book__author')
    readonly_fields = ('added_at',)
    autocomplete_fields = ['book']
    list_select_related = ('user', 'book')
    date_hierarchy = 'added_at'
    
    def book_title(self, obj):
        """Muestra el título del libro."""
        return obj.book.title
    book_title.short_description = 'Libro'
    book_title.admin_order_field = 'book__title'
    
    def book_author(self, obj):
        """Muestra el autor del libro."""
        return obj.book.author
    book_author.short_description = 'Autor'
    book_author.admin_order_field = 'book__author'