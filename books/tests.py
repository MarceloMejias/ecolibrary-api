# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Book


class BookModelTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title="Test Book", author="Tester", description="Desc",
            category="Test", publication_year=2024
        )

    def test_string_representation(self):
        self.assertEqual(str(self.book), "Test Book (2024)")

class BookAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book = Book.objects.create(
            title="API Book", author="API", description="Desc",
            category="API", publication_year=2024
        )
        self.url = '/api/books/local/' # Ajusta si tu ruta es diferente

    def test_get_books_public(self):
        """Cualquiera debería poder ver libros (REQ03)"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_book_unauthorized(self):
        """Sin ser admin, no se puede crear (REQ05)"""
        data = {'title': 'New', 'author': 'X', 'description': 'D', 'category': 'C', 'publication_year': 2025}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)