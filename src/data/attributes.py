from data.metadata import load_clean_metadata
from data.reviews import load_clean_reviews
from prompts import get_json_response, read_prompt
from app.settings import DATA_FOLDER
from app.utils import save_to_json, load_from_json
from functools import partial
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_games(with_reviews: bool):
    games = load_clean_metadata()
    reviewed_games = load_clean_reviews()

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
    
def generate_game_attributes(game_id, reviews, model, attr_system, attr_user, agg_system, agg_user):
    attributes = []

    for i, review in enumerate(reviews):
        attr_user_prompt = attr_user.format(review=review)

        try:
            attr = get_json_response(model, attr_system, attr_user_prompt)
            attributes.extend(attr)
        except:
            print(f"Error procesando atributos para ID: {game_id} (Reseña {i+1})")

    agg_user_prompt = agg_user.format(attributes="\n".join(attributes))
    try:
        return get_json_response(model, agg_system, agg_user_prompt)
    except Exception as e:
        print(e)
        print(f"Error generando lista final de atributos para ID: {game_id}")    

# Genera diccionario de juegos con atributos a partir de las reseñas
def generate_attributes(model, max_workers=None):
    reviews_dict = load_clean_reviews()
    attributes = load_attributes()

    pending_games = list(set(reviews_dict.keys()).difference(attributes.keys()))
    print("Total de juegos con reseñas:", len(reviews_dict))
    print("Total de juegos con atributos:", len(attributes))
    print("Juegos pendientes:", len(pending_games))

    total = len(pending_games)
    reviews = [reviews_dict[game_id] for game_id in pending_games]

    attr_system = read_prompt("attributes_system.txt")
    attr_user = read_prompt("attributes_user.txt")
    agg_system = read_prompt("aggregator_system.txt")
    agg_user = read_prompt("aggregator_user.txt")

    task = partial(
        generate_game_attributes,
        model=model,
        attr_system=attr_system,
        attr_user=attr_user,
        agg_system=agg_system,
        agg_user=agg_user
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task, gid, rev): gid for gid, rev in zip(pending_games, reviews)}

        for i, future in enumerate(as_completed(futures), 1):
            game_id = futures[future]
            
            result = future.result()
            if result is not None:
                attributes[game_id] = result

            p = (i / total) * 100
            print(f"[{i}/{total}] | {p:.2f}% completado | Finalizado: {game_id}")

            if i % 5 == 0: # Guardar cada 5 juegos
                print("Guardando...")
                save_to_json(DATA_FOLDER / "attributes.json", attributes)
    
    save_to_json(DATA_FOLDER / "attributes.json", attributes)
    print("✅ Finalizado.")

# Carga diccionario de juegos con sus atributos
def load_attributes():
    attributes = load_from_json(DATA_FOLDER / "attributes.json")
    if attributes is None:
        attributes = {}
    return attributes