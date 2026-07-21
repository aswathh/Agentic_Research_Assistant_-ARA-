from langchain_groq import ChatGroq
from src.core.config import settings


def get_llm(temperature: float = 0.0) -> ChatGroq:
    """Single point of construction for the LLM client.
    Every agent node imports from here — never instantiates ChatGroq directly.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
    )