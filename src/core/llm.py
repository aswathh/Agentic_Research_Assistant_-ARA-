from langchain_groq import ChatGroq
from src.core.config import Settings

def get_llm(temperatue:float=0.2)->ChatGroq:

    """Single point of construction for the LLM client.
    Every agent node imports from here — never instantiates ChatGroq directly.
    """
    return ChatGroq(
        api_key=Settings.groq_api_key,
        model=Settings.groq_model,
        temperature=temperature
    )