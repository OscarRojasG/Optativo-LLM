import requests
from app.utils import RequestError
from app.settings import IGDB_CLIENT_ID, IGDB_TOKEN, METADATA_FILENAME
import os
import json
import time

HEADERS = {
    'Client-ID': IGDB_CLIENT_ID,
    'Authorization': f'Bearer {IGDB_TOKEN}',
}

def get_games_count():
    url = "https://api.igdb.com/v4/games/count"
    query = "where game_type = 0 & summary != n & genres != n & total_rating_count >= 10;"

    response = requests.post(url, headers=HEADERS, data=query)
    return response.json()['count']

def fetch_batch(last_id):
    """Realiza una petición a IGDB pidiendo juegos con ID mayor a last_id."""

    query_template = """
        fields name, summary, storyline, total_rating, total_rating_count,
            genres.name, platforms.name, themes.name, 
            external_games.external_game_source, external_games.uid, 
            cover.url, game_type;
        where id > {last_id} 
            & game_type = 0 
            & summary != n 
            & genres != n 
            & total_rating_count >= 10;
        sort id asc;
        limit 500;
    """

    query = query_template.format(last_id=last_id)
    
    try:
        response = requests.post("https://api.igdb.com/v4/games", headers=HEADERS, data=query)
        response.raise_for_status()
        return response.json()
    except Exception:
        raise RequestError()
    
def save_to_json(data):
    """Guarda la lista completa de juegos en el archivo JSON."""
    with open(METADATA_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_json():
    """Carga los juegos existentes del archivo si existe."""
    if os.path.exists(METADATA_FILENAME):
        with open(METADATA_FILENAME, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def clear_data():
    """Elimina el archivo de metadata si existe."""
    if os.path.exists(METADATA_FILENAME):
        os.remove(METADATA_FILENAME)

def download_data():
    """Lee el archivo de metadata y continúa desde el último ID."""
    all_games = load_from_json()
    
    if not all_games:
        last_id = 0
    else:
        # Buscamos el ID más alto en la lista
        last_id = max(game['id'] for game in all_games)
    
    download_loop(all_games, last_id)

def download_loop(game_list, last_id=0):
    """Bucle principal de descarga con guardado preventivo."""
    while True:
        batch = fetch_batch(last_id)
        
        if batch is None: # Error de conexión, paramos pero guardamos lo que tenemos
            print("🛑 Error detectado. Guardando progreso y saliendo...")
            break
            
        if not batch: # No hay más resultados
            print("✅ ¡Descarga completada con éxito!")
            break
            
        game_list.extend(batch)
        last_id = batch[-1]['id'] # Actualizamos el checkpoint
        
        # Guardado preventivo en cada batch
        save_to_json(game_list)
        
        print(f"📦 Descargados {len(game_list)} juegos... (Último ID: {last_id})")
        
        # Respetamos el rate limit de 4 req/sec
        time.sleep(0.3)