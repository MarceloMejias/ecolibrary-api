"""
Serializadores de la aplicación Books.

Define los serializadores para los modelos Book y User,
convirtiendo objetos Django en JSON y viceversa.
"""

from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializador para el modelo Book.
    
    Expone todos los campos del modelo para lectura y escritura.
    Los campos created_at y updated_at son de solo lectura.
    """
    
    class Meta:
        model = Book
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de usuarios.
    
    Attributes:
        id (int): ID único del usuario (solo lectura).
        username (str): Nombre de usuario único.
        email (str): Correo electrónico del usuario.
        password (str): Contraseña (solo escritura, se encripta automáticamente).
    """
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        """
        Crea un nuevo usuario con la contraseña encriptada.
        
        Args:
            validated_data (dict): Datos validados del usuario.
        
        Returns:
            User: Instancia del usuario creado.
        """
        user = User.objects.create_user(**validated_data)
        return user