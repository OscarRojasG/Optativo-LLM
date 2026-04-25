from abc import ABC, abstractmethod
from app import utils
from app.utils import RequestError
from data import metadata
from app.settings import REVIEWS_FOLDER

class Scraper(ABC):
    @staticmethod
    @abstractmethod
    def name():
        pass

    @staticmethod
    @abstractmethod
    def get_reviews_by_id(id: str):
        pass

    @staticmethod
    @abstractmethod
    def clean_reviews(id: str):
        pass

    @staticmethod
    @abstractmethod
    def get_best_reviews(reviews: list):
        pass

    @classmethod
    def get_raw_reviews_filepath(cls):
        return REVIEWS_FOLDER / f'raw_{cls.name().lower()}_reviews.json'
    
    @classmethod
    def get_clean_reviews_filepath(cls):
        return REVIEWS_FOLDER / f'clean_{cls.name().lower()}_reviews.json'

    @classmethod
    def load_raw_reviews(cls):
        data = utils.load_from_json(cls.get_raw_reviews_filepath())
        return data if data else {}
    
    @classmethod
    def load_clean_reviews(cls):
        data = utils.load_from_json(cls.get_clean_reviews_filepath())
        return data if data else {}
    
    @classmethod
    def save_raw_reviews(cls, data):
        utils.save_to_json(cls.get_raw_reviews_filepath(), data)

    @classmethod
    def save_clean_reviews(cls, data):
        utils.save_to_json(cls.get_clean_reviews_filepath(), data)

    @staticmethod
    def get_pending_games(from_id):
        games = metadata.load_from_json()
        pending_games = []

        for game in games:
            if game['id'] <= from_id: continue
            if 'external_games' not in game: continue

            for platform in game['external_games']:
                if platform['external_game_source'] == 1:
                    pending_games.append({'igdb_id': game['id'], 'platform_id': platform['uid']})
                    break

        return pending_games
    
    @classmethod
    def download_reviews(cls):
        reviews_dict = cls.load_raw_reviews()
        
        if not reviews_dict:
            last_id = -1
        else:
            last_id = max([int(k) for k in reviews_dict])
        
        pending_games = cls.get_pending_games(from_id=last_id)
        cls.download_loop(reviews_dict, pending_games)

    @classmethod
    def download_loop(cls, reviews_dict, pending_games):
        """Bucle principal de descarga con guardado preventivo."""
        for game in pending_games:
            try:
                reviews = cls.get_reviews_by_id(game['platform_id'])
                reviews = cls.clean_reviews(reviews)
            except RequestError:
                print(f"📦 Descargadas reseñas para {len(reviews_dict)} juegos... (Último ID: {game['igdb_id']})")
                print("🛑 Error detectado. Guardando progreso y saliendo...")
                break
                
            reviews_dict[game['igdb_id']] = reviews
            cls.save_raw_reviews(reviews_dict)
            
            if len(reviews_dict) % 10 == 0:
                print(f"📦 Descargadas reseñas para {len(reviews_dict)} juegos... (Último ID: {game['igdb_id']})")

        print("✅ ¡Descarga completada con éxito!")

    @classmethod
    def filter_reviews(cls):
        all_reviews = cls.load_raw_reviews()
        filtered_reviews = {}

        for igdb_id, reviews in all_reviews.items():
            best_reviews = cls.get_best_reviews(reviews)
            best_reviews = [review.replace('\n', ' ').replace('\r', '') for review in best_reviews]
            if len(best_reviews) == 0: continue
            filtered_reviews[igdb_id] = best_reviews

        cls.save_clean_reviews(filtered_reviews)