from data.metadata import load_clean_metadata
from data.attributes import load_attributes
from prompts import read_prompt
from langchain_chroma.vectorstores import Chroma
from app.settings import CHROMADB_FOLDER
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.utils import save_to_json, load_from_json
from app.settings import DATA_FOLDER

def format_prompt(prompt, metadata, attributes):
    attributes_str = '\n'.join(attributes)
    return prompt.format(attributes=attributes_str, **metadata)

def build_document(metadata: dict, attributes: list[str]) -> str:
    attrs = ", ".join(attributes)
    return (
        f"{metadata['summary']} "
        f"{metadata['name']} is a {metadata['genres']} game from the {metadata['era']} era. "
        f"It features {metadata['themes'].lower()} themes, played from a {metadata['perspective'].lower()} perspective. "
        f"Challenge level: {metadata['challenge_level']}. "
        f"Key attributes: {attrs}."
    )

def generate_documents():
    all_metadata = load_clean_metadata()
    all_attributes = load_attributes()

    documents = []

    for game in all_attributes:
        metadata = all_metadata[game]
        attributes = all_attributes[game]
        documents.append(build_document(metadata, attributes))

    save_to_json(DATA_FOLDER / "documents.json", documents)

def load_documents():
    return load_from_json(DATA_FOLDER / "documents.json")

# Genera embeddings combinando metadata + atributos
def generate_embeddings(model, documents):
    # Guardar los embeddings
    Chroma.from_texts(
        texts=documents, 
        embedding=model, 
        persist_directory=CHROMADB_FOLDER,
        collection_metadata={"hnsw:space": "cosine"}
    )

def similarity_search(model, query, k):
    store = Chroma(persist_directory=CHROMADB_FOLDER, embedding_function=model, collection_metadata={"hnsw:space": "cosine"})
    results = store.similarity_search_with_relevance_scores(query, k=k)
    return results

def most_similar_game(model, query):
    return similarity_search(model, query, 1)[0]

def generate_tfidf_matrix(documents):
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    return tfidf_matrix, vectorizer

def lexical_search(documents, tfidf_matrix, vectorizer, query, k):
    query_vector = vectorizer.transform([query])
    cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    related_docs_indices = cosine_similarities.argsort()[:-k-1:-1]
    return [documents[index] for index in related_docs_indices]