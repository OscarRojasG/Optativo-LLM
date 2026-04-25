import requests
from app.utils import RequestError
from data.scraping.scraper import Scraper

class SteamScraper(Scraper):
    @staticmethod
    def name():
        return "Steam"
    
    @staticmethod
    def get_reviews_by_id(id: str):
        base_url = "https://store.steampowered.com/appreviews/{id}?json=1&filter=all&language=all&purchase_type=steam&num_per_page=20"
        url = base_url.format(id=id)

        response = requests.get(url)

        if response.status_code != 200:
            raise RequestError()

        data = response.json()

        if data['success'] == 0:
            raise RequestError()
        
        return data.get('reviews', [])

    @staticmethod
    def clean_reviews(raw_reviews):
        cleaned_data = []
        
        for r in raw_reviews:
            review_map = {
                "text": r.get("review").replace('\n', ' ').replace('\r', ''),
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

    @staticmethod
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
        
        # Ordenamos por score y devolvemos las top 5
        valid_reviews = sorted(valid_reviews, key=lambda x: x['score'], reverse=True)[:5]
        return [r['text'] for r in valid_reviews]