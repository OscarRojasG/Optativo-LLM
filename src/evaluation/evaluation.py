from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.run_config import RunConfig
from datasets import Dataset
from data.embeddings import similarity_search
from chatbot import translate_query, generate_final_response

def generate_evaluation_dataset(text_model, embedding_model, test_queries, references, k=10):
    data = []

    for user_query, reference in zip(test_queries, references):
        # Preprocesamiento: Traducir query a formato técnico
        structured_search_text = translate_query(text_model, user_query)
        
        # Recuperación: Buscar en ChromaDB
        results = similarity_search(embedding_model, structured_search_text, k)
        docs = [doc.page_content for doc, similarity in results]
        
        # Generación: El LLM redacta la recomendación final en español
        response = generate_final_response(text_model, docs[0], user_query)
        
        # Guardar datos para Ragas
        data.append({
            "question": user_query,        # Pregunta original del usuario
            "answer": response,            # Respuesta del chatbot
            "contexts": docs,              # Metadata y atributos del juego
            "reference": reference
        })

    return data

def evaluation(dataset_list, text_model, embedding_model, max_workers=1):
    # 1. Convertir tu lista a Dataset de HuggingFace
    ds = Dataset.from_list(dataset_list)
    
    # 2. Envolver tu modelo de LangChain
    # Ragas v0.2+ necesita que el wrapper sea explícito
    ragas_model = LangchainLLMWrapper(langchain_llm=text_model)
    ragas_emb = LangchainEmbeddingsWrapper(embeddings=embedding_model)

    config = RunConfig(
        timeout=600,
        max_workers=max_workers  
    )
    
    # 3. NO instancies las clases como Faithfulness() 
    # Usa los objetos ya creados que vienen en el paquete metrics
    metricas = [faithfulness, answer_relevancy]
    metricas = [faithfulness, answer_relevancy, context_precision, context_recall]
    
    # 4. Usar la función evaluate. 
    # Aquí es donde le pasas el modelo a TODAS las métricas de golpe.
    result = evaluate(
        dataset=ds,
        metrics=metricas,
        llm=ragas_model,
        embeddings=ragas_emb,
        run_config=config
    )
    
    return result