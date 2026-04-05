import json
import os

class RequestError(Exception):
    pass

def save_to_json(filepath, data):
    """Guarda la lista completa de juegos en el archivo JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

def delete_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)