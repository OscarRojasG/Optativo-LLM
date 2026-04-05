from google import genai
from app.settings import GEMINI_API_KEY

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(GEMINI_API_KEY)

def request(prompt: str):
    response = client.models.generate_content(
        model="gemini-3-flash-preview", contents=prompt
    )
    return response.text