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

def build_document(metadata: dict, attributes: list[str]) -> str:
    attrs = ", ".join(attributes)
    return (
        f"{metadata['summary']} "
        f"{metadata['name']} is a {metadata['genres']} game from the {metadata['era']} era. "
        f"It features {metadata['themes'].lower()} themes, played from a {metadata['perspective'].lower()} perspective. "
        f"Challenge level: {metadata['challenge_level']}. "
        f"Key attributes: {attrs if attrs else 'None'}."
    )

def generate_documents():
    all_metadata = load_clean_metadata()
    all_attributes = load_attributes()

    documents = []
    metadatas = []

    for game in all_metadata:
        metadata = all_metadata[game]
        attributes = all_attributes[game] if game in all_attributes else []
        
        documents.append(build_document(metadata, attributes))
        metadatas.append(all_metadata[game]) 

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