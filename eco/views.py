# IMPORTANTE: Importamos los modelos directamente (Arquitectura Monolito)
from books.models import Book, Favorite
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render


# Catalógico de Libros
def index(request):
    # Consulta directa a la DB
    books = Book.objects.all().order_by('-created_at')
    
    # Obtener favoritos del usuario si está autenticado
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('book_id', flat=True))
    
    return render(request, 'index.html', {'books': books, 'favorite_ids': favorite_ids})

# Detalle de Libro
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    
    is_favorite = False
    if request.user.is_authenticated:
        # Consulta ORM directa
        is_favorite = Favorite.objects.filter(user=request.user, book=book).exists()

    # Capturar el origen de navegación para la vista de retorno
    referer = request.GET.get('from', 'index')
    
    return render(request, 'book_detail.html', {
        'book': book,
        'is_favorite': is_favorite,
        'back_to': referer
    })

# Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.username}!")
            return redirect('index')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

# Registro
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Loguear automáticamente
            messages.success(request, "Registro exitoso.")
            return redirect('index')
        else:
            # UserCreationForm maneja los mensajes de error automáticamente
            messages.error(request, "Error en el registro. Revisa los datos.")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})

# Logout
def logout_view(request):
    logout(request)
    messages.info(request, "Sesión cerrada.")
    return redirect('index')

# Favoritos
@login_required
def toggle_favorite_web(request, book_id):
    """
    Acción para dar like/dislike. 
    Se llama 'toggle_favorite_web' para coincidir con tu urls.py.
    """
    book = get_object_or_404(Book, pk=book_id)
    fav, created = Favorite.objects.get_or_create(user=request.user, book=book)
    
    if not created:
        fav.delete()
        messages.warning(request, "Libro eliminado de favoritos")
    else:
        messages.success(request, "Libro agregado a favoritos")
    
    # Redirigir al origen si viene de favoritos
    referer = request.GET.get('from', 'index')
    if referer == 'favorites':
        return redirect('favorites')
    
    return redirect('book_detail', book_id=book_id)

# Mis Favoritos
@login_required
def favorites_view(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('book')
    books = [f.book for f in favorites]
    return render(request, 'favorites.html', {'books': books})