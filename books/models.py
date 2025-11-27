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
            # Si tenemos external_id, buscar directamente
            if self.external_id:
                work_data = None
                edition_data = None
                
                # Detectar si es un Edition ID (libro) o Work ID
                is_edition = 'M' in self.external_id.upper()
                is_work = 'W' in self.external_id.upper()
                
                print(f"DEBUG: Procesando external_id: {self.external_id} (Edition: {is_edition}, Work: {is_work})")
                
                # Si es una edición (book), obtener el work asociado
                if is_edition:
                    try:
                        # Limpiar y formatear el ID de edición
                        clean_id = self.external_id.replace("OL", "").replace("M", "")
                        edition_url = f"https://openlibrary.org/books/OL{clean_id}M.json"
                        
                        edition_response = requests.get(edition_url, timeout=5)
                        if edition_response.status_code == 200:
                            edition_data = edition_response.json()
                            print(f"DEBUG: Edición obtenida: {edition_data.get('title')}")
                            
                            # Obtener el work key de la edición
                            works = edition_data.get('works', [])
                            if works and len(works) > 0:
                                work_key = works[0].get('key', '')
                                if work_key:
                                    work_url = f"https://openlibrary.org{work_key}.json"
                                    work_response = requests.get(work_url, timeout=5)
                                    if work_response.status_code == 200:
                                        work_data = work_response.json()
                                        print(f"DEBUG: Work obtenido desde edición: {work_data.get('title')}")
                    except Exception as e:
                        print(f"Error obteniendo edición: {e}")
                
                # Si es un work o no pudimos obtener datos de la edición
                if is_work or not work_data:
                    try:
                        # Limpiar el external_id de prefijos si los tiene
                        clean_id = self.external_id.replace("OL", "").replace("W", "")
                        work_url = f"https://openlibrary.org/works/OL{clean_id}W.json"
                        
                        response = requests.get(work_url, timeout=5)
                        response.raise_for_status()
                        work_data = response.json()
                    except Exception:
                        # Si falla con formato OL###W, intentar con el ID tal cual
                        try:
                            work_url = f"https://openlibrary.org/works/{self.external_id}.json"
                            response = requests.get(work_url, timeout=5)
                            response.raise_for_status()
                            work_data = response.json()
                        except Exception as e:
                            print(f"Error obteniendo work: {e}")
                
                # Procesar datos del work si existen
                if work_data:
                    
                    print("DEBUG: Work data obtenida")
                    print(f"  - Título en API: {work_data.get('title', 'N/A')}")
                    print(f"  - Descripción existe: {bool(work_data.get('description'))}")
                    print(f"  - Subjects: {len(work_data.get('subjects', []))} encontrados")
                    print(f"  - Covers: {len(work_data.get('covers', []))} encontradas")
                    
                    # Actualizar título (priorizar work, luego edition)
                    if not self.title or self.title == "" or self.title == "Sin título":
                        self.title = work_data.get("title") or (edition_data.get("title") if edition_data else None) or "Sin título"
                        print(f"  ✓ Título actualizado: {self.title}")
                    
                    # Obtener autores
                    if "authors" in work_data and work_data["authors"]:
                        author_keys = []
                        for author_ref in work_data["authors"]:
                            if isinstance(author_ref, dict) and "author" in author_ref:
                                key = author_ref["author"].get("key", "")
                                if key:
                                    author_keys.append(key)
                        
                        authors = []
                        for key in author_keys[:3]:  # Máximo 3 autores
                            try:
                                author_url = f"https://openlibrary.org{key}.json"
                                author_response = requests.get(author_url, timeout=3)
                                if author_response.status_code == 200:
                                    author_data = author_response.json()
                                    name = author_data.get("name", "")
                                    if name:
                                        authors.append(name)
                            except Exception:
                                continue
                        
                        if authors and (not self.author or self.author == "" or self.author == "Autor desconocido"):
                            self.author = ", ".join(authors)
                            print(f"  ✓ Autor(es) actualizado: {self.author}")
                    
                    # Descripción
                    if not self.description or self.description == "" or self.description == "Sin descripción disponible":
                        description = work_data.get("description")
                        if description:
                            if isinstance(description, dict):
                                desc_value = description.get("value", "")
                                if desc_value:
                                    self.description = desc_value
                                    print(f"  ✓ Descripción actualizada (dict): {len(self.description)} caracteres")
                            elif isinstance(description, str):
                                self.description = description
                                print(f"  ✓ Descripción actualizada (str): {len(self.description)} caracteres")
                    
                    # Si no hay descripción del work, intentar obtener de la primera edición
                    if not self.description or self.description == "Sin descripción disponible":
                        # Si ya tenemos edition_data, usarla
                        if edition_data:
                            ed_desc = edition_data.get("description")
                            if ed_desc:
                                if isinstance(ed_desc, dict):
                                    self.description = ed_desc.get("value", self.description)
                                else:
                                    self.description = ed_desc
                        else:
                            # Buscar ediciones si no tenemos edition_data
                            try:
                                work_id = work_data.get('key', '').split('/')[-1]
                                editions_url = f"https://openlibrary.org/works/{work_id}/editions.json"
                                editions_response = requests.get(editions_url, params={"limit": 1}, timeout=3)
                                if editions_response.status_code == 200:
                                    editions_data = editions_response.json()
                                    entries = editions_data.get("entries", [])
                                    if entries:
                                        first_edition = entries[0]
                                        ed_desc = first_edition.get("description")
                                        if ed_desc:
                                            if isinstance(ed_desc, dict):
                                                self.description = ed_desc.get("value", self.description)
                                            else:
                                                self.description = ed_desc
                                        elif "notes" in first_edition:
                                            notes = first_edition.get("notes")
                                            if isinstance(notes, dict):
                                                self.description = notes.get("value", self.description)
                                            elif isinstance(notes, str):
                                                self.description = notes
                            except Exception:
                                pass
                    
                    # Categorías/Subjects - intentar de múltiples fuentes
                    if not self.category or self.category == "" or self.category == "General":
                        subjects = work_data.get("subjects", [])
                        
                        # Si no hay subjects en el work, intentar de la edición
                        if not subjects and edition_data:
                            subjects = edition_data.get("subjects", [])
                        
                        if subjects:
                            self.category = ", ".join(subjects[:2])
                            print(f"  ✓ Categoría actualizada: {self.category}")
                        else:
                            # Si no hay subjects, intentar usar subject_places o dejar como "Sin categoría"
                            subject_places = work_data.get("subject_places", [])
                            if subject_places:
                                self.category = ", ".join(subject_places[:2])
                                print(f"  ✓ Categoría actualizada (places): {self.category}")
                    
                    # Año de primera publicación
                    if not self.publication_year or self.publication_year == 2000:
                        import re
                        
                        # Priorizar la fecha de la edición si la tenemos
                        if edition_data and edition_data.get("publish_date"):
                            pub_date = edition_data.get("publish_date")
                            year_match = re.search(r'\d{4}', str(pub_date))
                            if year_match:
                                self.publication_year = int(year_match.group())
                                print(f"  ✓ Año actualizado (de edición): {self.publication_year}")
                        
                        # Si no, buscar la fecha de la PRIMERA edición (más antigua)
                        if not self.publication_year or self.publication_year == 2000:
                            try:
                                work_id = work_data.get('key', '').split('/')[-1]
                                if not work_id.startswith('OL'):
                                    work_id = f"OL{work_id}"
                                if not work_id.endswith('W'):
                                    work_id = f"{work_id}W"
                                
                                # Obtener todas las ediciones para buscar la más antigua
                                editions_url = f"https://openlibrary.org/works/{work_id}/editions.json"
                                editions_response = requests.get(editions_url, params={"limit": 50}, timeout=3)
                                if editions_response.status_code == 200:
                                    editions_data = editions_response.json()
                                    entries = editions_data.get("entries", [])
                                    
                                    # Buscar el año más antiguo
                                    oldest_year = None
                                    for edition in entries:
                                        pub_date = edition.get("publish_date")
                                        if pub_date:
                                            year_match = re.search(r'\d{4}', str(pub_date))
                                            if year_match:
                                                year = int(year_match.group())
                                                if oldest_year is None or year < oldest_year:
                                                    oldest_year = year
                                    
                                    if oldest_year:
                                        self.publication_year = oldest_year
                                        print(f"  ✓ Año actualizado (primera edición): {self.publication_year}")
                            except Exception as e:
                                print(f"Error obteniendo año: {e}")
                    
                    # Portada - priorizar edición MÁS RECIENTE
                    if not self.cover_url or self.cover_url == "":
                        cover_found = False
                        
                        # Primero intentar de la edición actual si la tenemos
                        if edition_data:
                            covers = edition_data.get("covers", [])
                            valid_covers = [c for c in covers if c and c > 0]
                            if valid_covers:
                                self.cover_url = f"https://covers.openlibrary.org/b/id/{valid_covers[0]}-L.jpg"
                                print(f"  ✓ Portada actualizada (de edición actual): {self.cover_url}")
                                cover_found = True
                        
                        # Si no, buscar en las ediciones más recientes del work
                        if not cover_found:
                            try:
                                work_id = work_data.get('key', '').split('/')[-1]
                                if not work_id.startswith('OL'):
                                    work_id = f"OL{work_id}"
                                if not work_id.endswith('W'):
                                    work_id = f"{work_id}W"
                                
                                # Obtener ediciones para buscar las más recientes con portada
                                editions_url = f"https://openlibrary.org/works/{work_id}/editions.json"
                                editions_response = requests.get(editions_url, params={"limit": 50}, timeout=3)
                                if editions_response.status_code == 200:
                                    editions_data = editions_response.json()
                                    entries = editions_data.get("entries", [])
                                    
                                    # Ordenar ediciones por año de publicación (más reciente primero)
                                    import re
                                    editions_with_year = []
                                    for edition in entries:
                                        pub_date = edition.get("publish_date")
                                        year = None
                                        if pub_date:
                                            year_match = re.search(r'\d{4}', str(pub_date))
                                            if year_match:
                                                year = int(year_match.group())
                                        
                                        ed_covers = edition.get("covers", [])
                                        valid_ed_covers = [c for c in ed_covers if c and c > 0]
                                        
                                        if valid_ed_covers:
                                            editions_with_year.append({
                                                'year': year or 0,
                                                'cover_id': valid_ed_covers[0]
                                            })
                                    
                                    # Ordenar por año descendente y tomar la más reciente
                                    if editions_with_year:
                                        editions_with_year.sort(key=lambda x: x['year'], reverse=True)
                                        newest = editions_with_year[0]
                                        self.cover_url = f"https://covers.openlibrary.org/b/id/{newest['cover_id']}-L.jpg"
                                        print(f"  ✓ Portada actualizada (edición más reciente, año {newest['year']}): {self.cover_url}")
                                        cover_found = True
                            except Exception as e:
                                print(f"Error obteniendo portada de ediciones: {e}")
                        
                        # Como último recurso, usar la portada del work
                        if not cover_found:
                            covers = work_data.get("covers", [])
                            valid_covers = [c for c in covers if c and c > 0]
                            if valid_covers:
                                self.cover_url = f"https://covers.openlibrary.org/b/id/{valid_covers[0]}-L.jpg"
                                print(f"  ✓ Portada actualizada (de work): {self.cover_url}")
                    
                    print("DEBUG: Fetch completado exitosamente")
                    return True
            
            # Si no hay external_id, buscar por título
            if self.title and self.title != "Sin título":
                search_url = "https://openlibrary.org/search.json"
                response = requests.get(
                    search_url,
                    params={"title": self.title, "limit": 1},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    docs = data.get("docs", [])
                    
                    if docs:
                        book = docs[0]
                        
                        # Actualizar external_id
                        work_key = book.get("key", "")
                        if work_key:
                            self.external_id = work_key.split("/")[-1]
                        
                        # Autores
                        authors = book.get("author_name", [])
                        if authors:
                            self.author = ", ".join(authors[:3])
                        
                        # Año de publicación
                        year = book.get("first_publish_year")
                        if year:
                            self.publication_year = year
                        
                        # Categorías
                        subjects = book.get("subject", [])
                        if subjects:
                            self.category = ", ".join(subjects[:2])
                        
                        # Portada
                        cover_id = book.get("cover_i")
                        if cover_id:
                            self.cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                        
                        # Ahora que tenemos el external_id, llamar recursivamente para obtener descripción
                        if self.external_id:
                            return self.fetch_book_data_from_openlibrary()
                        
                        return True
            
            return False
            
        except Exception as e:
            # Log del error para debugging
            print(f"Error fetching from OpenLibrary: {e}")
            return False

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