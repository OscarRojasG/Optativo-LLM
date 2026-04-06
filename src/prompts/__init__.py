from google import genai
from google.genai import types
from app.settings import GEMINI_API_KEY, SYSTEM_PROMPTS_FOLDER, USER_PROMPTS_FOLDER


# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key=GEMINI_API_KEY)

def send_prompt(user_prompt: str, system_prompt: str, model: str):
    args = {
        "model": model,
        "contents": user_prompt
    }
    if system_prompt:
        args["config"] = types.GenerateContentConfig(
            system_instruction = system_prompt
        )

    response = client.models.generate_content(**args)
    return response.text

def read_system_prompt(filename: str):
    return _read_prompt(f"{SYSTEM_PROMPTS_FOLDER}/{filename}")

def read_user_prompt(filename: str):
    return _read_prompt(f"{USER_PROMPTS_FOLDER}/{filename}")

def _read_prompt(filepath: str):
    with open(filepath, "r") as f:
        return f.read()