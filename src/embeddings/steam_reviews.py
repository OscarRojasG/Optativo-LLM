import requests
from app import utils
from app.utils import RequestError
from embeddings import igdb_metadata
from app.settings import RAW_STEAM_REVIEWS_FILENAME, CLEAN_STEAM_REVIEWS_FILENAME

def get_steam_reviews_by_id(id: str):
    base_url = "https://store.steampowered.com/appreviews/{id}?json=1&filter=all&language=all&purchase_type=steam&num_per_page=20"
    url = base_url.format(id=id)

    response = requests.get(url)

    if response.status_code != 200:
        raise RequestError()

    data = response.json()

    if data['success'] == 0:
        raise RequestError()
    
    return data.get('reviews', [])

def save_to_json(data):
    utils.save_to_json(RAW_STEAM_REVIEWS_FILENAME, data)

def load_from_json():
    data = utils.load_from_json(RAW_STEAM_REVIEWS_FILENAME)
    return data if data else {}

def clear_data():
    utils.delete_file(RAW_STEAM_REVIEWS_FILENAME)

def get_pending_games(from_id):
    games = igdb_metadata.load_from_json()
    pending_games = []

    for game in games:
        if game['id'] <= from_id: continue
        if 'external_games' not in game: continue

        for platform in game['external_games']:
            if platform['external_game_source'] == 1:
                pending_games.append({'igdb_id': game['id'], 'platform_id': platform['uid']})
                break

    return pending_games

def download_reviews():
    reviews_dict = load_from_json()
    
    if not reviews_dict:
        last_id = -1
    else:
        last_id = max([int(k) for k in reviews_dict])
    
    pending_games = get_pending_games(from_id=last_id)
    download_loop(reviews_dict, pending_games)

def clean_reviews(raw_reviews):
    cleaned_data = []
    
    for r in raw_reviews:
        review_map = {
            "text": r.get("review"),
            "is_positive": r.get("voted_up"),
            "score": r.get("weighted_vote_score"),
            "playtime_hours": round(r.get("author").get("playtime_at_review", 0) / 60),
            "votes_useful": r.get("votes_up"),
            "votes_funny": r.get("votes_funny"),
            "is_free": r.get("received_for_free"),
            "early_access": r.get("written_during_early_access")
        }

        if review_map["text"] and len(review_map["text"].strip()) > 0:
            cleaned_data.append(review_map)
            
    return cleaned_data

def download_loop(reviews_dict, pending_games):
    """Bucle principal de descarga con guardado preventivo."""
    for game in pending_games:
        try:
            reviews = get_steam_reviews_by_id(game['platform_id'])
            reviews = clean_reviews(reviews)
        except RequestError:
            print(f"📦 Descargadas reseñas para {len(reviews_dict)} juegos... (Último ID: {game['igdb_id']})")
            print("🛑 Error detectado. Guardando progreso y saliendo...")
            break
            
        reviews_dict[game['igdb_id']] = reviews
        save_to_json(reviews_dict)
        
        if len(reviews_dict) % 10 == 0:
            print(f"📦 Descargadas reseñas para {len(reviews_dict)} juegos... (Último ID: {game['igdb_id']})")

    print("✅ ¡Descarga completada con éxito!")

def get_best_reviews(reviews):
    valid_reviews = []
    for r in reviews:
        # 1. Filtro de longitud mínima
        if len(r['text']) < 150: continue
        
        # 2. Filtro anti-meme
        if r['votes_funny'] > r['votes_useful'] and r['votes_funny'] > 5: continue

        # 3. Filtro de playtime
        if r['playtime_hours'] == 0: continue
        
        # 4. Cálculo de score de calidad
        score = float(r['score']) * 100
        score += min(len(r['text']) / 100, 20) # Bonus por detalle (máx 20pts)
        
        valid_reviews.append({
            'text': r['text'],
            'score': score
        })
    
    # Ordenamos por nuestro score y devolvemos las top 5
    return sorted(valid_reviews, key=lambda x: x['score'], reverse=True)[:5]

def filter_reviews():
    all_reviews = load_from_json()
    filtered_reviews = {}

    for igdb_id, reviews in all_reviews.items():
        best_reviews = get_best_reviews(reviews)
        if len(best_reviews) == 0: continue
        filtered_reviews[igdb_id] = [r['text'] for r in best_reviews]

    utils.save_to_json(CLEAN_STEAM_REVIEWS_FILENAME, filtered_reviews)

def get_filtered_reviews():
    return utils.load_from_json(CLEAN_STEAM_REVIEWS_FILENAME)