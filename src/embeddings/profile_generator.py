from embeddings.igdb_metadata import load_clean_metadata
from embeddings.scraping import SteamScraper
from prompts import send_prompt, read_system_prompt, read_user_prompt

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

def generate_profiles_without_reviews(user_prompt_filename: str, system_prompt_filename: str, model: str):
    games_without_reviews = get_games(with_reviews=False)
    system_prompt = read_system_prompt(system_prompt_filename)
    user_prompt = read_user_prompt(user_prompt_filename)

    game = games_without_reviews[0]
    user_prompt = format_user_prompt_metadata(user_prompt, game)

    response = send_prompt(user_prompt, system_prompt, model)
    print(response)

def generate_profiles_with_reviews(user_prompt_filename: str, system_prompt_filename: str, model: str):
    games_with_reviews = get_games(with_reviews=True)
    system_prompt = read_system_prompt(system_prompt_filename)
    user_prompt = read_user_prompt(user_prompt_filename)

    game = games_with_reviews[0]

    for i in range(len(game['reviews'])):
        game['reviews'][i] = f"{i+1}. {game['reviews'][i].replace('\n', ' ')}"

    user_prompt = format_user_prompt_metadata(user_prompt, game)

    response = send_prompt(user_prompt, system_prompt, model)
    print(response)