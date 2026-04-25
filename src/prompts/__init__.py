from typing import Optional
from langchain.chat_models import BaseChatModel
from langchain.embeddings import Embeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import BaseOutputParser, StrOutputParser, JsonOutputParser
from app.settings import PROMPTS_FOLDER


def get_response(model: BaseChatModel, system_prompt: Optional[str], user_prompt: str, output_parser: BaseOutputParser):
    messages = []

    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    
    messages.append(HumanMessage(content=user_prompt))

    chain = model | output_parser
    return chain.invoke(messages)

def get_text_response(model: BaseChatModel, system_prompt: str, user_prompt: str):
    return get_response(model, system_prompt, user_prompt, StrOutputParser())

def get_json_response(model: BaseChatModel, system_prompt: str, user_prompt: str):
    return get_response(model, system_prompt, user_prompt, JsonOutputParser())

def get_embedding(model: Embeddings, input: str):
    return model.embed_query(input)

def read_prompt(filepath: str):
    with open(PROMPTS_FOLDER / filepath, "r") as f:
        return f.read()