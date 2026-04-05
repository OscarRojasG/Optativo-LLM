from dotenv import load_dotenv
import os
import requests

load_dotenv()

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
    print(data)
    return data['access_token']

IGDB_TOKEN = get_igdb_token(IGDB_CLIENT_ID, IGDB_CLIENT_SECRET)