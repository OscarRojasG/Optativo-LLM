from data.metadata import load_clean_metadata
from data.scraping import SteamScraper
from prompts import get_json_response, read_prompt
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from app.settings import DATA_FOLDER
from app.utils import save_to_json, load_from_json

def get_games(with_reviews: bool):
    games = load_clean_metadata()
    reviewed_games = SteamScraper.load_clean_reviews()

    filtered_games = []
    for id, game in games.items():
        is_reviewed = id in reviewed_games
        
        if is_reviewed == with_reviews:
            if is_reviewed:
                game['reviews'] = reviewed_games[id]
            filtered_games.append(game)
            
    return filtered_games

def format_user_prompt_metadata(user_prompt, game):
    return user_prompt.format(
        name = game['name'],
        era = game['era'],
        genres = game['genres'],
        themes = game['themes'],
        perspective = game['perspective'],
        is_vr = game['is_vr'],
        is_multiplayer = game['is_multiplayer'],
        challenge_level = game['challenge_level'],
        critic_score = game['critic_score'],
        summary = game['summary'].replace("\n", " "),
        storyline = game['storyline'].replace("\n", " "),
        reviews = "\n".join(game['reviews'])
    )

def load_clean_reviews():
    return SteamScraper.load_clean_reviews()

def generate_game_attributes(game_name, reviews, model, system_prompt, user_prompt):
    reviews_text = "\n".join([
        f"{i+1}. {review}" 
        for i, review in enumerate(reviews) 
        if review.strip()
    ])
    user_prompt = user_prompt.format(game_name=game_name, reviews=reviews_text)

    try:
        return get_json_response(model, system_prompt, user_prompt)
    except:
        print(f"Error procesando atributos para: {game_name}")
        return None

# Genera diccionario de juegos con atributos a partir de las reseñas
def generate_attributes(model, max_workers=1):
    games = load_clean_metadata()
    reviews_dict = load_clean_reviews()

    names = [] 
    reviews = []
    for game_id in list(reviews_dict.keys())[:10]:
        names.append(games[game_id]['name'])
        reviews.append(reviews_dict[game_id])

    system_prompt = read_prompt("attributes_system.txt")
    user_prompt = read_prompt("attributes_user.txt")

    task = partial(
        generate_game_attributes,
        model=model,
        system_prompt=system_prompt, 
        user_prompt=user_prompt
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(task, names, reviews))

    attributes_dict = {}
    for game_id, result in zip(list(games.keys()), results):
        if result is None: continue
        attributes_dict[game_id] = result

    save_to_json(DATA_FOLDER / "attributes.json", attributes_dict)
    return results

# Carga diccionario de juegos con sus atributos
def load_attributes():
    return load_from_json(DATA_FOLDER / "attributes.json")