import requests


def search_open_library(query):
    """
    Busca libros en Open Library API y retorna una lista limpia con portadas.
    """
    if not query:
        return []

    url = "https://openlibrary.org/search.json"
    params = {
        "q": query,
        "limit": 10,
        "fields": "key,title,author_name,first_publish_year,cover_i,isbn,subject"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return []

    cleaned_books = []
    
    for item in data.get("docs", []):
        # Extraer el ID de Open Library del key
        work_key = item.get("key", "").split("/")[-1]
        
        # Construir URL de portada si existe cover_i
        cover_id = item.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
        
        # Extraer autores
        authors = item.get("author_name", ["Desconocido"])
        author_str = ", ".join(authors[:3])  # Máximo 3 autores
        
        # Extraer categorías/subjects
        subjects = item.get("subject", ["General"])
        category = ", ".join(subjects[:2]) if subjects else "General"
        
        book_data = {
            "external_id": work_key,
            "title": item.get("title", "Sin título"),
            "author": author_str,
            "description": f"Publicado en {item.get('first_publish_year', 'año desconocido')}",
            "publication_year": item.get("first_publish_year", 0) or 0,
            "cover_url": cover_url,
            "category": category
        }
        cleaned_books.append(book_data)

    return cleaned_books