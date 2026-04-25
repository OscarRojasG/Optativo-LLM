from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

class OllamaTextModel(ChatOllama):
    pass
    
class GeminiTextModel(ChatGoogleGenerativeAI):
    def __init__(self, model, temperature):
        load_dotenv()
        super().__init__(
            model=model,
            temperature=temperature,
            api_key=os.getenv("GEMINI_API_KEY"))