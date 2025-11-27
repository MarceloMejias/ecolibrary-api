"""
Serializadores de la aplicación Books.

Define los serializadores para los modelos Book y User,
convirtiendo objetos Django en JSON y viceversa.
"""

from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Book.
    
    Expone todos los campos del modelo para lectura y escritura.
    Los campos created_at y updated_at son de solo lectura.
    Incluye cover_url_auto que obtiene la portada automáticamente.
    """
    
    cover_url_auto = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def get_cover_url_auto(self, obj):
        return obj.get_cover_url()


class EmptySerializer(serializers.Serializer):
    pass