import requests
from app.misc import RequestError
from app.settings import IGDB_CLIENT_ID, IGDB_TOKEN


def get_igdb_metadata():
    headers = {
        'Client-ID': IGDB_CLIENT_ID,
        'Authorization': f'Bearer {IGDB_TOKEN}',
    }

    query = "fields name, rating, summary; where rating > 80; limit 10;"

    response = requests.post("https://api.igdb.com/v4/games", headers=headers, data=query)

    if response.status_code != 200:
        raise RequestError()
    
    return response.json()