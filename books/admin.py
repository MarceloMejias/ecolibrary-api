from django.contrib import admin, messages

from .models import Book, Favorite


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'publication_year', 'has_cover')
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
    list_display = ('user', 'book', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'book__title')