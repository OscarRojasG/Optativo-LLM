from prompts import read_prompt, get_text_response

def translate_query(model, query):
    system_prompt = read_prompt("query_translation.txt")
    return get_text_response(model, system_prompt, query)

def generate_final_response(model, document, query):
    template = read_prompt("recommendation.txt")
    prompt = template.format(document=document, query=query)
    return get_text_response(model, None, prompt)