from pathlib import Path
import requests

def get_igdb_token(client_id, client_secret):
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, params=params)
    data = response.json()
    return data['access_token']

# RUTAS
PROJECT_ROOT = Path(__file__).parent.parent.parent

DATA_FOLDER = PROJECT_ROOT / "data"
REVIEWS_FOLDER = DATA_FOLDER / "reviews"

PROMPTS_FOLDER = PROJECT_ROOT / "prompts"

RAW_REVIEWS_FILEPATH = DATA_FOLDER / "raw_reviews.json"
CLEAN_REVIEWS_FILEPATH = DATA_FOLDER / "clean_reviews.json"

RAW_METADATA_FILEPATH = DATA_FOLDER / "raw_metadata.json"
CLEAN_METADATA_FILEPATH = DATA_FOLDER / "clean_metadata.json"

CHROMADB_FOLDER = PROJECT_ROOT / "chromadb"