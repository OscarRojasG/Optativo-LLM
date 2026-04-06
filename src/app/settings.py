from dotenv import load_dotenv
from pathlib import Path
import os
import requests

load_dotenv()


# CLAVES
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IGDB_CLIENT_ID = os.getenv("IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("IGDB_CLIENT_SECRET")


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

IGDB_TOKEN = get_igdb_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)


# RUTAS
PROJECT_ROOT = Path.cwd().parent

DATA_FOLDER = PROJECT_ROOT / "data"
REVIEWS_FOLDER = DATA_FOLDER / "reviews"

PROMPTS_FOLDER = PROJECT_ROOT / "prompts"
SYSTEM_PROMPTS_FOLDER = PROMPTS_FOLDER / "system"
USER_PROMPTS_FOLDER = PROMPTS_FOLDER / "user"

RAW_METADATA_FILEPATH = DATA_FOLDER / "raw_metadata.json"
CLEAN_METADATA_FILEPATH = DATA_FOLDER / "clean_metadata.json"