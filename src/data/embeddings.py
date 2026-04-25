from data.metadata import load_clean_metadata
from data.attributes import load_attributes
from prompts import read_prompt
from langchain_chroma.vectorstores import Chroma
from app.settings import CHROMADB_FOLDER
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def format_prompt(prompt, metadata, attributes):
    attributes_str = '\n'.join(attributes)
    return prompt.format(attributes=attributes_str, **metadata)

def generate_documents():
    all_metadata = load_clean_metadata()
    all_attributes = load_attributes()

    prompt = read_prompt("document.txt")
    documents = []

    for game in all_attributes:
        metadata = all_metadata[game]
        attributes = all_attributes[game]

        attributes_str = '\n'.join(attributes)
        document = prompt.format(attributes=attributes_str, **metadata)
        documents.append(document)

    return documents

# Genera embeddings combinando metadata + atributos
def generate_embeddings(model):
    documents = generate_documents()

    # Guardar los embeddings
    Chroma.from_texts(
        texts=documents, 
        embedding=model, 
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