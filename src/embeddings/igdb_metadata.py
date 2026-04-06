import requests
from app import utils
from app.utils import RequestError
from app.settings import IGDB_CLIENT_ID, IGDB_TOKEN, RAW_METADATA_FILEPATH, CLEAN_METADATA_FILEPATH
import time
from datetime import datetime

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
        fields name, summary, storyline, total_rating, first_release_date,
            genres.name, 
            platforms.name, 
            themes.name, 
            game_modes.name, 
            player_perspectives.name,
            keywords.name,
            collection.name,
            involved_companies.company.name, 
            involved_companies.developer,
            age_ratings.rating,
            external_games.external_game_source, 
            external_games.url;
        where id > {last_id} 
            & game_type = 0 
            & summary != n 
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
    
def save_raw_metadata(data):
    utils.save_to_json(RAW_METADATA_FILEPATH, data)

def load_raw_metadata():
    data = utils.load_from_json(RAW_METADATA_FILEPATH)
    return data if data else []

def save_clean_metadata(data):
    utils.save_to_json(CLEAN_METADATA_FILEPATH, data)

def load_clean_metadata():
    return utils.load_from_json(CLEAN_METADATA_FILEPATH)

def download_data():
    """Lee el archivo de metadata y continúa desde el último ID."""
    all_games = load_raw_metadata()
    
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
        save_raw_metadata(game_list)
        
        print(f"📦 Descargados {len(game_list)} juegos... (Último ID: {last_id})")
        
        # Respetamos el rate limit de 4 req/sec
        time.sleep(0.3)

def get_clean_metadata(game_data):
    """Transforma el JSON de IGDB en un formato enriquecido para Gemini."""
    
    # 1. Extracción básica de nombres
    genres = [g['name'] for g in game_data.get('genres', [])]
    platforms = [p['name'] for p in game_data.get('platforms', [])]
    themes = [t['name'] for t in game_data.get('themes', [])]
    perspectives = [p['name'] for p in game_data.get('player_perspectives', [])]
    game_modes = [m['name'] for m in game_data.get('game_modes', [])]
    
    # 2. Lógica de Realidad Virtual (VR)
    vr_keywords = ['VR', 'Virtual Reality', 'Quest', 'Oculus', 'Mixed Reality', 'SteamVR']
    is_vr = any(any(kw in p for kw in vr_keywords) for p in platforms)
    
    # 3. Lógica Social (Multijugador)
    # Si tiene modos que no sean "Single player", lo marcamos como multijugador
    multi_modes = ['Multiplayer', 'Co-operative', 'Split screen', 'Massively Multiplayer Online (MMO)']
    is_multiplayer = any(mode in multi_modes for mode in game_modes)
    
    # 4. Estimación de Nivel de Desafío (Heurística)
    # Buscamos géneros o temas que suelen implicar dificultad alta
    hard_keywords = ['Roguelike', 'Soulslike', 'Tactical', 'Strategy', 'Fighting', 'Simulator']
    challenge_tags = [tag for tag in hard_keywords if tag in genres or tag in themes]
    challenge_level = "Alto / Técnico" if challenge_tags else "Estándar / Accesible"
    
    # 5. Clasificación por Era (Basado en el año de lanzamiento)
    release_ts = game_data.get('first_release_date')
    if release_ts:
        year = datetime.fromtimestamp(release_ts).year
        if year < 1995: era = "Retro (8/16-bit)"
        elif 1995 <= year <= 2005: era = "Clásica (3D Temprano)"
        elif 2006 <= year <= 2015: era = "Moderna"
        else: era = "Contemporánea / Next-Gen"
    else:
        era = "Desconocida"

    return {
        "name": game_data.get('name'),
        "era": era,
        "genres": ", ".join(genres),
        "themes": ", ".join(themes),
        "perspective": perspectives[0] if perspectives else "No especificada",
        "is_vr": "Sí" if is_vr else "No",
        "is_multiplayer": "Sí" if is_multiplayer else "No",
        "challenge_level": challenge_level,
        "critic_score": round(game_data.get('total_rating', 0)),
        "summary": game_data.get('summary', 'No disponible'),
        "storyline": game_data.get('storyline', 'No disponible')
    }

def generate_clean_metadata():
    raw_metadata = load_raw_metadata()
    clean_metadata = {game['id']: get_clean_metadata(game) for game in raw_metadata}
    save_clean_metadata(clean_metadata)