import requests
from app.misc import RequestError

def get_steam_reviews(id: str):
    base_url = "https://store.steampowered.com/appreviews/{id}?json=1&language=spanish&review_type=positive"
    url = base_url.format(id=id)

    response = requests.get(url)

    if response.status_code != 200:
        raise RequestError()

    data = response.json()

    if data['success'] == 0:
        raise RequestError()
    
    return [review['review'] for review in data['reviews']]