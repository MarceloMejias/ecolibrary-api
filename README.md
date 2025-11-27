# EcoLibrary

Sistema de gestión de biblioteca digital con integración a Open Library API. Proyecto monolítico Django con frontend web y API REST.

## Características

- **Catálogo de Libros**: Búsqueda y visualización de libros desde Open Library
- **Gestión de Favoritos**: Los usuarios pueden marcar libros como favoritos
- **API REST**: Endpoints para integración con aplicaciones externas
- **Autenticación**: Sistema de registro y login con tokens
- **Panel de Administración**: Gestión completa desde Django Admin

## Stack Tecnológico

- **Backend**: Django 5.2.8
- **API**: Django REST Framework
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5.3 (Bootswatch Lux theme)
- **Iconos**: Font Awesome 6.4.2
- **Integración Externa**: Open Library API

## Requisitos Previos

- Python 3.13+
- uv (gestor de paquetes)
- Git

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/MarceloMejias/ecolibrary-base.git
cd ecolibrary-base
```

### 2. Instalar dependencias

```bash
cd core_api
uv sync
```

### 3. Aplicar migraciones

```bash
python manage.py migrate
```

### 4. Crear superusuario

```bash
python manage.py createsuperuser
```

### 5. Ejecutar el servidor

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://localhost:8000`

## Endpoints API REST

### Libros

- `GET /api/books/local/` - Listar todos los libros
- `GET /api/books/local/{id}/` - Detalle de un libro
- `POST /api/books/local/` - Crear libro (admin)
- `PUT/PATCH /api/books/local/{id}/` - Actualizar libro (admin)
- `DELETE /api/books/local/{id}/` - Eliminar libro (admin)

### Favoritos

- `GET /api/books/local/my_favorites/` - Ver mis favoritos (requiere autenticación)
- `POST /api/books/local/{id}/toggle_favorite/` - Agregar/quitar favorito (requiere autenticación)

### Búsqueda Externa

- `GET /api/books/external-search/?q=query` - Buscar libros en Open Library

### Autenticación

- `POST /api/books/login/` - Obtener token de autenticación
  ```json
  {
    "username": "usuario",
    "password": "contraseña"
  }
  ```

### Uso del Token

Incluir en el header de las peticiones:

```
Authorization: Token <tu_token>
```

## Frontend Web

- **Inicio**: `/` - Catálogo de libros
- **Detalle**: `/book/{id}/` - Información detallada del libro
- **Favoritos**: `/favorites/` - Libros favoritos del usuario
- **Login**: `/login/` - Iniciar sesión
- **Registro**: `/register/` - Crear cuenta
- **Admin**: `/admin/` - Panel de administración (superusuarios)

## Estructura del Proyecto

```
ecolibrary/
├── core_api/              # Proyecto Django principal
│   ├── books/             # App de gestión de libros (API)
│   │   ├── models.py      # Modelos Book y Favorite
│   │   ├── views.py       # Vistas API REST
│   │   ├── serializers.py # Serializadores DRF
│   │   ├── services.py    # Integración Open Library
│   │   └── urls.py        # Rutas API
│   ├── eco/               # App frontend web
│   │   ├── views.py       # Vistas web
│   │   ├── templates/     # Plantillas HTML
│   │   └── urls.py        # Rutas frontend
│   └── core/              # Configuración del proyecto
│       ├── settings.py
│       └── urls.py
├── docker-compose.yaml    # Configuración Docker
└── README.md
```

## Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# --- Configuración Django ---
DJANGO_SECRET_KEY=iPhone4G-
DEBUG=True
SUPER_SECRET_KEY=django-insecure-8vk4+!Szfi+8@$$pccesg%-y-53&s1@mr!4@v71olzzyjg8&
ALLOWED_HOSTS=*
```

## Integración con Open Library

El sistema se integra automáticamente con Open Library API para obtener:

- Información completa de libros (título, autor, descripción, categoría)
- Año de primera publicación (busca en hasta 50 ediciones)
- Portada (prioriza ediciones más recientes)
- Soporte para Work IDs (`OL###W`) y Edition IDs (`OL###M`)

