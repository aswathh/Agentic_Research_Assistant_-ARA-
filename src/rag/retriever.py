from langchain_core.documents import Document
from src.rag.vectorstore import get_vectorstore


def retrieve(query: str, k: int = 4) -> list[Document]:
    """Thin retrieval interface — this is the only function agent code should call.
    Keeping vectorstore details out of agent code means we can swap Chroma for
    Pinecone/pgvector later without touching a single agent file.
    """
    store = get_vectorstore()
    return store.similarity_search(query, k=k)


def format_context(docs: list[Document]) -> str:
    """Turn retrieved docs into a single string block for prompt injection."""
    return "\n\n".join(f"[Source: {d.metadata.get('source', 'unknown')}]\n{d.page_content}" for d in docs)