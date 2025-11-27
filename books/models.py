"""
Modelos de la aplicación Books.

Define los modelos Book y Favorite para el catálogo de libros
y la gestión de favoritos de usuarios.
"""

import requests
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
    title = models.CharField(max_length=255, blank=True, verbose_name="Título")
    author = models.CharField(max_length=255, blank=True, verbose_name="Autor")
    description = models.TextField(blank=True, verbose_name="Descripción breve")
    category = models.CharField(max_length=100, blank=True, verbose_name="Categoría")
    publication_year = models.PositiveIntegerField(blank=True, null=True, verbose_name="Año de publicación")
    
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
        verbose_name="URL de Portada (opcional)"
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_cover_url(self):
        """
        Obtiene la URL de la portada automáticamente desde Open Library.
        Si cover_url está definido manualmente, lo usa. Si no, busca en Open Library.
        """
        # Si ya tiene una portada manual, usarla
        if self.cover_url:
            return self.cover_url
        
        # Buscar en Open Library por título y autor
        try:
            response = requests.get(
                "https://openlibrary.org/search.json",
                params={
                    "title": self.title,
                    "author": self.author,
                    "limit": 1
                },
                timeout=3
            )
            data = response.json()
            
            if data.get("docs"):
                cover_id = data["docs"][0].get("cover_i")
                if cover_id:
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        except Exception:
            pass
        
        return None

    def fetch_book_data_from_openlibrary(self):
        """
        Busca y rellena automáticamente todos los campos del libro desde Open Library
        usando el external_id. Soporta tanto Work IDs (OL###W) como Edition IDs (OL###M).
        Si external_id no está presente, busca por título.
        
        Returns:
            bool: True si se encontró y actualizó la información, False en caso contrario.
        """
        try:
            if self.external_id:
                return self._fetch_by_external_id()
            elif self.title and self.title != "Sin título":
                return self._fetch_by_title()
            return False
        except Exception as e:
            print(f"Error fetching from OpenLibrary: {e}")
            return False

    def _fetch_by_external_id(self):
        """Obtiene datos usando external_id."""
        work_data, edition_data = self._get_work_and_edition_data()
        
        if not work_data:
            return False
        
        self._update_from_work_data(work_data, edition_data)
        return True

    def _fetch_by_title(self):
        """Obtiene datos buscando por título."""
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={"title": self.title, "limit": 1},
            timeout=5
        )
        
        if response.status_code != 200:
            return False
        
        docs = response.json().get("docs", [])
        if not docs:
            return False
        
        book = docs[0]
        self._update_from_search_result(book)
        
        if self.external_id:
            return self.fetch_book_data_from_openlibrary()
        return True

    def _get_work_and_edition_data(self):
        """Obtiene datos de work y edition desde Open Library."""
        is_edition = 'M' in self.external_id.upper()
        work_data = None
        edition_data = None
        
        if is_edition:
            edition_data = self._fetch_edition_data()
            if edition_data:
                work_data = self._fetch_work_from_edition(edition_data)
        
        if not work_data:
            work_data = self._fetch_work_data()
        
        return work_data, edition_data

    def _fetch_edition_data(self):
        """Obtiene datos de una edición específica."""
        try:
            clean_id = self.external_id.replace("OL", "").replace("M", "")
            url = f"https://openlibrary.org/books/OL{clean_id}M.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error obteniendo edición: {e}")
        return None

    def _fetch_work_from_edition(self, edition_data):
        """Obtiene el work asociado a una edición."""
        try:
            works = edition_data.get('works', [])
            if works:
                work_key = works[0].get('key', '')
                if work_key:
                    url = f"https://openlibrary.org{work_key}.json"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        return response.json()
        except Exception as e:
            print(f"Error obteniendo work desde edición: {e}")
        return None

    def _fetch_work_data(self):
        """Obtiene datos de un work directamente."""
        try:
            clean_id = self.external_id.replace("OL", "").replace("W", "")
            url = f"https://openlibrary.org/works/OL{clean_id}W.json"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception:
            try:
                url = f"https://openlibrary.org/works/{self.external_id}.json"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error obteniendo work: {e}")
        return None

    def _update_from_work_data(self, work_data, edition_data):
        """Actualiza los campos del modelo desde los datos obtenidos."""
        self._update_title(work_data, edition_data)
        self._update_author(work_data)
        self._update_description(work_data, edition_data)
        self._update_category(work_data, edition_data)
        self._update_publication_year(work_data, edition_data)
        self._update_cover_url(work_data, edition_data)

    def _update_title(self, work_data, edition_data):
        """Actualiza el título del libro."""
        if self.title and self.title != "" and self.title != "Sin título":
            return
        
        title = work_data.get("title")
        if not title and edition_data:
            title = edition_data.get("title")
        
        self.title = title or "Sin título"

    def _update_author(self, work_data):
        """Actualiza el autor del libro."""
        if self.author and self.author != "" and self.author != "Autor desconocido":
            return
        
        authors = work_data.get("authors", [])
        if not authors:
            return
        
        author_names = []
        for author_ref in authors[:3]:
            if isinstance(author_ref, dict) and "author" in author_ref:
                key = author_ref["author"].get("key", "")
                if key:
                    name = self._fetch_author_name(key)
                    if name:
                        author_names.append(name)
        
        if author_names:
            self.author = ", ".join(author_names)

    def _fetch_author_name(self, author_key):
        """Obtiene el nombre de un autor desde su key."""
        try:
            url = f"https://openlibrary.org{author_key}.json"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                return response.json().get("name", "")
        except Exception:
            pass
        return None

    def _update_description(self, work_data, edition_data):
        """Actualiza la descripción del libro."""
        if self.description and self.description != "" and self.description != "Sin descripción disponible":
            return
        
        description = self._extract_description(work_data.get("description"))
        
        if not description and edition_data:
            description = self._extract_description(edition_data.get("description"))
        
        if not description:
            description = self._fetch_description_from_editions(work_data)
        
        if description:
            self.description = description

    def _extract_description(self, description):
        """Extrae el texto de descripción desde diferentes formatos."""
        if not description:
            return None
        
        if isinstance(description, dict):
            return description.get("value", "")
        elif isinstance(description, str):
            return description
        return None

    def _fetch_description_from_editions(self, work_data):
        """Busca descripción en las ediciones del work."""
        try:
            work_id = work_data.get('key', '').split('/')[-1]
            url = f"https://openlibrary.org/works/{work_id}/editions.json"
            response = requests.get(url, params={"limit": 1}, timeout=3)
            
            if response.status_code == 200:
                entries = response.json().get("entries", [])
                if entries:
                    first_edition = entries[0]
                    desc = self._extract_description(first_edition.get("description"))
                    if desc:
                        return desc
                    return self._extract_description(first_edition.get("notes"))
        except Exception:
            pass
        return None

    def _update_category(self, work_data, edition_data):
        """Actualiza la categoría del libro."""
        if self.category and self.category != "" and self.category != "General":
            return
        
        subjects = work_data.get("subjects", [])
        
        if not subjects and edition_data:
            subjects = edition_data.get("subjects", [])
        
        if subjects:
            self.category = ", ".join(subjects[:2])
        else:
            subject_places = work_data.get("subject_places", [])
            if subject_places:
                self.category = ", ".join(subject_places[:2])

    def _update_publication_year(self, work_data, edition_data):
        """Actualiza el año de publicación."""
        if self.publication_year and self.publication_year != 2000:
            return
        
        year = self._extract_year_from_edition(edition_data)
        
        if not year:
            year = self._fetch_oldest_year(work_data)
        
        if year:
            self.publication_year = year

    def _extract_year_from_edition(self, edition_data):
        """Extrae el año de publicación de una edición."""
        import re
        
        if not edition_data:
            return None
        
        pub_date = edition_data.get("publish_date")
        if pub_date:
            year_match = re.search(r'\d{4}', str(pub_date))
            if year_match:
                return int(year_match.group())
        return None

    def _fetch_oldest_year(self, work_data):
        """Busca el año de la edición más antigua."""
        import re
        
        try:
            work_id = self._normalize_work_id(work_data.get('key', '').split('/')[-1])
            url = f"https://openlibrary.org/works/{work_id}/editions.json"
            response = requests.get(url, params={"limit": 50}, timeout=3)
            
            if response.status_code == 200:
                entries = response.json().get("entries", [])
                oldest_year = None
                
                for edition in entries:
                    pub_date = edition.get("publish_date")
                    if pub_date:
                        year_match = re.search(r'\d{4}', str(pub_date))
                        if year_match:
                            year = int(year_match.group())
                            if oldest_year is None or year < oldest_year:
                                oldest_year = year
                
                return oldest_year
        except Exception as e:
            print(f"Error obteniendo año: {e}")
        return None

    def _update_cover_url(self, work_data, edition_data):
        """Actualiza la URL de portada."""
        if self.cover_url and self.cover_url != "":
            return
        
        cover_id = self._get_cover_from_edition(edition_data)
        
        if not cover_id:
            cover_id = self._fetch_newest_cover(work_data)
        
        if not cover_id:
            cover_id = self._get_cover_from_work(work_data)
        
        if cover_id:
            self.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    def _get_cover_from_edition(self, edition_data):
        """Obtiene cover ID de una edición."""
        if not edition_data:
            return None
        
        covers = edition_data.get("covers", [])
        valid_covers = [c for c in covers if c and c > 0]
        return valid_covers[0] if valid_covers else None

    def _get_cover_from_work(self, work_data):
        """Obtiene cover ID del work."""
        covers = work_data.get("covers", [])
        valid_covers = [c for c in covers if c and c > 0]
        return valid_covers[0] if valid_covers else None

    def _fetch_newest_cover(self, work_data):
        """Busca la portada de la edición más reciente."""
        import re
        
        try:
            work_id = self._normalize_work_id(work_data.get('key', '').split('/')[-1])
            url = f"https://openlibrary.org/works/{work_id}/editions.json"
            response = requests.get(url, params={"limit": 50}, timeout=3)
            
            if response.status_code == 200:
                entries = response.json().get("entries", [])
                editions_with_covers = []
                
                for edition in entries:
                    year = self._extract_year_from_edition(edition)
                    cover_id = self._get_cover_from_edition(edition)
                    
                    if cover_id:
                        editions_with_covers.append({'year': year or 0, 'cover_id': cover_id})
                
                if editions_with_covers:
                    editions_with_covers.sort(key=lambda x: x['year'], reverse=True)
                    return editions_with_covers[0]['cover_id']
        except Exception as e:
            print(f"Error obteniendo portada de ediciones: {e}")
        return None

    def _normalize_work_id(self, work_id):
        """Normaliza el work ID al formato OL###W."""
        if not work_id.startswith('OL'):
            work_id = f"OL{work_id}"
        if not work_id.endswith('W'):
            work_id = f"{work_id}W"
        return work_id

    def _update_from_search_result(self, book):
        """Actualiza campos desde resultado de búsqueda."""
        work_key = book.get("key", "")
        if work_key:
            self.external_id = work_key.split("/")[-1]
        
        authors = book.get("author_name", [])
        if authors:
            self.author = ", ".join(authors[:3])
        
        year = book.get("first_publish_year")
        if year:
            self.publication_year = year
        
        subjects = book.get("subject", [])
        if subjects:
            self.category = ", ".join(subjects[:2])
        
        cover_id = book.get("cover_i")
        if cover_id:
            self.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para auto-rellenar campos desde Open Library
        si external_id está presente y los campos básicos están vacíos.
        """
        # Si tenemos external_id pero faltan campos básicos, rellenarlos automáticamente
        if self.external_id:
            # Verificar si faltan campos importantes
            needs_fetch = (
                not self.title or 
                not self.author or 
                not self.description or 
                not self.category or 
                not self.publication_year
            )
            
            if needs_fetch:
                fetch_success = self.fetch_book_data_from_openlibrary()
                # Debug: imprimir qué se obtuvo
                if fetch_success:
                    print(f"Fetch exitoso - Título: {self.title}, Autor: {self.author}, Año: {self.publication_year}, Categoría: {self.category[:50] if self.category else 'None'}")
                else:
                    print("Fetch falló")
        
        # Si aún faltan campos requeridos después del fetch, poner valores por defecto
        if not self.title or self.title == "":
            self.title = "Sin título"
        if not self.author or self.author == "":
            self.author = "Autor desconocido"
        if not self.description or self.description == "":
            self.description = "Sin descripción disponible"
        if not self.category or self.category == "":
            self.category = "General"
        if not self.publication_year:
            self.publication_year = 2000
        
        super().save(*args, **kwargs)

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