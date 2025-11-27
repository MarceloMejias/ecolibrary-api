from unittest.mock import Mock, patch

import requests  # Importante para simular excepciones reales
from django.test import Client, TestCase
from django.urls import reverse


class ServicesTest(TestCase):
    @patch('eco.services.requests.get') # Ajusta 'eco' por el nombre de tu app si es distinto
    def test_api_get_failure(self, mock_get):
        """api_get debe retornar None cuando la API falla."""
        from eco.services import api_get
        
        # CORRECCIÓN: Usar RequestException en lugar de Exception genérica
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = api_get('local/')
        self.assertIsNone(result)

    @patch('eco.services.requests.get')
    def test_api_get_success(self, mock_get):
        from eco.services import api_get
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{'title': 'Libro 1'}]
        mock_get.return_value = mock_response

        result = api_get('local/')
        self.assertEqual(result, [{'title': 'Libro 1'}])

    @patch('eco.services.requests.post')
    def test_api_post_failure(self, mock_post):
        """api_post debe retornar None cuando la API falla."""
        from eco.services import api_post
        
        # CORRECCIÓN: Usar RequestException
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        result = api_post('register/', {})
        self.assertIsNone(result)

    @patch('eco.services.requests.post')
    def test_api_post_success(self, mock_post):
        from eco.services import api_post
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = api_post('register/', {})
        self.assertEqual(result.status_code, 201)

class WebViewsTest(TestCase):
    def setUp(self):
        self.client = Client()

    # ========== INDEX VIEW ==========
    def test_index_view(self):
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = []
            response = self.client.get(reverse('index'))
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'index.html')

    def test_index_view_api_error(self):
        """Index debe manejar error de conexión con la API."""
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = None
            response = self.client.get(reverse('index'))
            self.assertEqual(response.status_code, 200)
            self.assertIn('books', response.context)
            self.assertEqual(response.context['books'], [])

    def test_index_view_with_empty_list(self):
        """Index con lista vacía debe mostrar mensaje de error."""
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = []
            response = self.client.get(reverse('index'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['books'], [])
            messages = list(response.context['messages'])
            self.assertTrue(any('No se pudo conectar' in str(m) for m in messages))

    # ========== LOGIN VIEW ==========
    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

    def test_login_view_already_authenticated(self):
        """Usuario ya autenticado debe redirigir a index."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_login_view_post_invalid_form(self):
        """Login con formulario inválido debe mostrar errores."""
        response = self.client.post(reverse('login'), {
            'username': '',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'This field is required.')

    def test_login_view_post_success(self):
        """Login exitoso debe guardar token en sesión y redirigir."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'token': 'test-token-123'}
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'testpass'
            })
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('index'))
            self.assertEqual(self.client.session['auth_token'], 'test-token-123')
            self.assertEqual(self.client.session['user_data']['username'], 'testuser')

    def test_login_view_post_no_token_in_response(self):
        """Login con respuesta sin token debe mostrar error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('login'), {
                'username': 'testuser',
                'password': 'testpass'
            })
            
            self.assertEqual(response.status_code, 200)
            messages = list(response.context['messages'])
            self.assertTrue(any('Error al procesar' in str(m) for m in messages))

    def test_login_view_post_invalid_credentials(self):
        """Login con credenciales incorrectas debe mostrar error."""
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('login'), {
                'username': 'wronguser',
                'password': 'wrongpass'
            })
            
            self.assertEqual(response.status_code, 200)
            messages = list(response.context['messages'])
            self.assertTrue(any('incorrectos' in str(m) for m in messages))

    # ========== REGISTER VIEW ==========
    def test_register_view_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

    def test_register_view_already_authenticated(self):
        """Usuario ya autenticado debe redirigir a index."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))

    def test_register_view_post_success(self):
        """Registro exitoso debe redirigir al login."""
        mock_response = Mock()
        mock_response.status_code = 201
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('register'), {
                'username': 'newuser',
                'email': 'newuser@test.com',
                'password': 'newpass123'
            })
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('login'))

    def test_register_view_post_failure(self):
        """Registro fallido debe mostrar error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'username': ['Usuario existe']}
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('register'), {
                'username': 'existing',
                'email': 'test@test.com',
                'password': 'pass'
            })
            
            self.assertEqual(response.status_code, 200)
            messages = list(response.context['messages'])
            self.assertIn('Usuario existe', str(messages[0]))

    def test_register_view_post_invalid_form(self):
        """Registro con formulario inválido debe mostrar errores."""
        response = self.client.post(reverse('register'), {
            'username': '',
            'email': 'invalid-email',
            'password': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'This field is required.')

    # ========== LOGOUT VIEW ==========
    def test_logout_view(self):
        """Logout debe borrar sesión y redirigir."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session['user_data'] = {'username': 'testuser'}
        session.save()
        
        response = self.client.post(reverse('logout'))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('index'))
        self.assertNotIn('auth_token', self.client.session)
        self.assertNotIn('user_data', self.client.session)

    # ========== BOOK DETAIL VIEW ==========
    def test_book_detail_view_success(self):
        """Book detail debe mostrar libro encontrado."""
        mock_book = {
            'id': 1,
            'title': 'Test Book',
            'authors': 'Test Author',
            'description': 'Test description'
        }
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = mock_book
            
            response = self.client.get(reverse('book_detail', args=[1]))
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'book_detail.html')
            self.assertEqual(response.context['book'], mock_book)
            self.assertFalse(response.context['is_favorite'])

    def test_book_detail_view_not_found(self):
        """Book detail con libro no encontrado debe redirigir."""
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = None
            
            response = self.client.get(reverse('book_detail', args=[999]))
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('index'))

    def test_book_detail_view_book_is_none(self):
        """Book detail con book=None debe redirigir a index."""
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = None
            
            response = self.client.get(reverse('book_detail', args=[1]))
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('index'))
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any('no encontrado' in str(m) for m in messages))

    def test_book_detail_view_with_favorite(self):
        """Book detail debe marcar libro como favorito si aplica."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        mock_book = {'id': 1, 'title': 'Test Book'}
        mock_favorites = [{'id': 1, 'title': 'Test Book'}]
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.side_effect = [mock_book, mock_favorites]
            
            response = self.client.get(reverse('book_detail', args=[1]))
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context['is_favorite'])

    def test_book_detail_view_not_favorite(self):
        """Book detail debe marcar libro como no favorito si no está en lista."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        mock_book = {'id': 1, 'title': 'Test Book'}
        mock_favorites = [{'id': 2, 'title': 'Other Book'}]
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.side_effect = [mock_book, mock_favorites]
            
            response = self.client.get(reverse('book_detail', args=[1]))
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['is_favorite'])

    def test_book_detail_view_favorites_api_error(self):
        """Book detail debe manejar error al obtener favoritos."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        mock_book = {'id': 1, 'title': 'Test Book'}
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.side_effect = [mock_book, None]
            
            response = self.client.get(reverse('book_detail', args=[1]))
            
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.context['is_favorite'])

    # ========== FAVORITES VIEW ==========
    def test_favorites_view_not_authenticated(self):
        """Favorites sin autenticación debe redirigir a login."""
        response = self.client.get(reverse('favorites'))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_favorites_view_success(self):
        """Favorites debe mostrar lista de favoritos del usuario."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session['user_data'] = {'username': 'testuser'}
        session.save()
        
        mock_favorites = [
            {'id': 1, 'title': 'Favorite 1'},
            {'id': 2, 'title': 'Favorite 2'}
        ]
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = mock_favorites
            
            response = self.client.get(reverse('favorites'))
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'favorites.html')
            self.assertEqual(response.context['books'], mock_favorites)

    def test_favorites_view_api_error(self):
        """Favorites debe manejar error de API."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = None
            
            response = self.client.get(reverse('favorites'))
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['books'], [])

    def test_favorites_view_empty_list(self):
        """Favorites con lista vacía debe mostrar mensaje."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        with patch('eco.views.api_get') as mock_api:
            mock_api.return_value = []
            
            response = self.client.get(reverse('favorites'))
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['books'], [])
            messages = list(response.context['messages'])
            self.assertTrue(any('Error al cargar' in str(m) for m in messages))

    # ========== TOGGLE FAVORITE VIEW ==========
    def test_toggle_favorite_success(self):
        """Usuario autenticado puede agregar/quitar favoritos."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'Agregado a favoritos'}
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('toggle_favorite', args=[1]))
            
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('book_detail', args=[1]))

    def test_toggle_favorite_not_authenticated(self):
        """Toggle favorite sin autenticación debe redirigir a login."""
        response = self.client.post(reverse('toggle_favorite', args=[1]))
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))

    def test_toggle_favorite_api_error(self):
        """Toggle favorite debe manejar error de API."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = mock_response
            
            response = self.client.post(reverse('toggle_favorite', args=[1]))
            
            self.assertEqual(response.status_code, 302)
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any('No se pudo actualizar' in str(m) for m in messages))

    def test_toggle_favorite_api_none_response(self):
        """Toggle favorite debe manejar respuesta None de API."""
        session = self.client.session
        session['auth_token'] = 'test-token'
        session.save()
        
        with patch('eco.views.api_post') as mock_api:
            mock_api.return_value = None
            
            response = self.client.post(reverse('toggle_favorite', args=[1]))
            
            self.assertEqual(response.status_code, 302)
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any('No se pudo actualizar' in str(m) for m in messages))