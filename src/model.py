from functools import lru_cache
from configparser import ConfigParser
from openai import OpenAI
import torch

MODEL_NAME = "gpt-5.2"

def _pick_dtype():

    """
    Pick the appropriate torch dtype based on device availability.
    """

    if torch.cuda.is_available():
        return torch.bfloat16
    return torch.float32

@lru_cache(maxsize=1)
def get_openai_client():
    config = ConfigParser()
    config.read("config.ini")
    key = config.get("openai", "api_key", fallback="")
    if not key:
        raise ValueError("Missing openai.api_key in config.ini")
    return OpenAI(api_key=key)



def chat_with_oss_python_block(system_prompt, user_prompt, max_new_tokens=500):

    """
    
    inputs
    :param system_prompt: System prompt for the chat
    :param user_prompt: User prompt for the chat
    :param max_new_tokens: Maximum number of tokens to generate

    returns
    :return: Generated text with <python>...</python> delimiters
    """

    client = get_openai_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,     # <-- puoi cambiare modello se vuoi
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_completion_tokens=max_new_tokens,
        temperature=0.7
    )

    # Estrai contenuto
    text = response.choices[0].message.content

    # Assicura delimitatori <python>...</python>
    if "<python>" not in text:
        text = "<python>" + text
    if "</python>" not in text:
        text = text + "</python>"

    return text
