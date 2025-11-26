import requests

def search_google_books(query):
    """
    Busca libros en Google Books API y retorna una lista limpia.
    """
    if not query:
        return []

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": query,
        "maxResults": 5, # Limitamos a 5 para no saturar
        "printType": "books"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        return [] # Si falla Google, retornamos lista vacía sin romper nada

    cleaned_books = []
    
    # Procesamos los resultados crudos de Google
    for item in data.get("items", []):
        volume_info = item.get("volumeInfo", {})
        
        # Extraemos la imagen de portada (si existe)
        image_links = volume_info.get("imageLinks", {})
        cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail")

        # Armamos un diccionario limpio para nuestro sistema
        book_data = {
            "google_id": item.get("id"),
            "title": volume_info.get("title", "Sin título"),
            "author": ", ".join(volume_info.get("authors", ["Desconocido"])),
            "description": volume_info.get("description", "Sin descripción"),
            "publication_year": volume_info.get("publishedDate", "")[:4], # Solo el año
            "cover_url": cover_url,
            "category": ", ".join(volume_info.get("categories", ["General"]))
        }
        cleaned_books.append(book_data)

    return cleaned_books