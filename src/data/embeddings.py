from data.metadata import load_clean_metadata
from data.attributes import load_attributes
from langchain_chroma.vectorstores import Chroma
from app.settings import CHROMADB_FOLDER
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.utils import load_from_json
from app.settings import DATA_FOLDER

def format_prompt(prompt, metadata, attributes):
    attributes_str = '\n'.join(attributes)
    return prompt.format(attributes=attributes_str, **metadata)

def is_valid_value(value) -> bool:
    """
    Verifica si un valor de metadata es útil.
    Retorna False para nulos, vacíos o valores genéricos de 'no disponible'.
    """
    if not value:
        return False
        
    if isinstance(value, str):
        # Limpiamos y pasamos a minúsculas para comparar de forma segura
        val_clean = value.strip().lower()
        valores_invalidos = ["not available", "not specified", "unknown", "n/a", "none"]
        if val_clean in valores_invalidos or val_clean == "":
            return False
            
    return True

def build_document(metadata: dict, attributes: list[str]) -> str:
    """
    Construye la sopa de texto omitiendo los campos que no aportan
    información (valores inválidos/vacíos).
    """
    parts = []
    
    # 1. Summary (Solo si existe y es válido)
    if is_valid_value(metadata.get('summary')):
        parts.append(f"{metadata['summary']}")
        
    # 2. Nombre, Género y Era
    name = metadata.get('name', 'Unknown Game')
    genres = metadata.get('genres', '')
    era = metadata.get('era', '')
    
    # Construimos la oración central manejando qué pasa si falta el género o la era
    base_sentence = f"{name} is a game"
    if is_valid_value(genres) and is_valid_value(era):
        base_sentence = f"{name} is a {genres} game from the {era} era."
    elif is_valid_value(genres):
        base_sentence = f"{name} is a {genres} game."
    elif is_valid_value(era):
         base_sentence = f"{name} is a game from the {era} era."
         
    parts.append(base_sentence)
    
    # 3. Temáticas y Perspectiva (Opcionales)
    themes = metadata.get('themes', '')
    perspective = metadata.get('perspective', '')
    
    if is_valid_value(themes) and is_valid_value(perspective):
        parts.append(f"It features {themes.lower()} themes, played from a {perspective.lower()} perspective.")
    elif is_valid_value(themes):
        parts.append(f"It features {themes.lower()} themes.")
    elif is_valid_value(perspective):
        parts.append(f"It is played from a {perspective.lower()} perspective.")

    # 4. Nivel de Desafío (Opcional)
    challenge = metadata.get('challenge_level', '')
    if is_valid_value(challenge):
        parts.append(f"Challenge level: {challenge}.")

    # 5. Atributos Extraídos (La parte más importante)
    if attributes:
        attrs = ", ".join(attributes)
        parts.append(f"Key attributes: {attrs}.")
        
    # Unimos todas las partes válidas con un espacio
    return " ".join(parts)

# La función generate_documents se mantiene igual:
def generate_documents():
    all_metadata = load_clean_metadata()
    all_attributes = load_attributes()

    documents = []
    metadatas = []

    for game in all_metadata:
        metadata = all_metadata[game]
        attributes = all_attributes[game] if game in all_attributes else []
        
        # Opcional: También puedes limpiar la metadata antes de guardarla en la lista
        # metadata = {k: v for k, v in metadata.items() if is_valid_value(v)}
        
        metadata['key_attributes'] = ", ".join(attributes)
        
        documents.append(build_document(metadata, attributes))
        metadatas.append(metadata) 

    return documents, metadatas

def generate_embeddings(model):
    documents, metadatas = generate_documents() # Recibimos ambas

    # Guardamos los embeddings CON sus metadatos
    Chroma.from_texts(
        texts=documents, 
        embedding=model, 
        metadatas=metadatas,
        persist_directory=CHROMADB_FOLDER
    )

def similarity_search(model, query, k):
    store = Chroma(persist_directory=CHROMADB_FOLDER, embedding_function=model)
    results = store.similarity_search_with_relevance_scores(query, k=k)
    return results

def generate_tfidf_matrix(documents):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    return tfidf_matrix, vectorizer

def lexical_search(documents, tfidf_matrix, vectorizer, query, k):
    query_vector = vectorizer.transform([query])
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    related_docs_indices = cosine_similarities.argsort()[:-k-1:-1]
    return [documents[index] for index in related_docs_indices]

def load_documents():
    return load_from_json(DATA_FOLDER / "documents.json")