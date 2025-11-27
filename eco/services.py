import os

import requests

# Leemos la URL interna definida en docker-compose (http://api:8000)
API_BASE_URL = os.environ.get('API_INTERNAL_URL', 'http://api:8000')

def get_headers(request):
    """
    Si el usuario está logueado, inyectamos su Token en la cabecera
    para que la API sepa quién es.
    """
    token = request.session.get('auth_token')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Token {token}'
    return headers

def api_get(endpoint, request=None, params=None):
    url = f"{API_BASE_URL}/api/books/{endpoint}"
    try:
        # Si pasamos request, inyectamos headers de auth
        headers = get_headers(request) if request else {}
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status() # Lanza error si no es 200 OK
        return response.json()
    except requests.RequestException:
        return None # Retorna None si falla la conexión

def api_post(endpoint, data, request=None):
    url = f"{API_BASE_URL}/api/books/{endpoint}"
    try:
        headers = get_headers(request) if request else {'Content-Type': 'application/json'}
        response = requests.post(url, json=data, headers=headers, timeout=5)
        return response # Retornamos el objeto response completo para validar status
    except requests.RequestException:
        return None