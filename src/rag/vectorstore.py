from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from src.core.config import settings

_embeddings=None

def get_embeddings():
    """Lazy singleton — loading the embedding model is slow, do it once."""
    global _embeddings
    if _embeddings is None:
        _embeddings=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings

def get_vectorstore():
    return Chroma(
        collection_name="ara_knowledge_base",
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_persist_dir,
    )
# Why a singleton for the embedding model: it's loaded into memory once and reused — reinstantiating it on every call would reload the model from disk each time, which is slow and wasteful.