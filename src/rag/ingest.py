from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from src.rag.vectorstore import get_vectorstore
from src.observability.logging_config import get_logger

logger = get_logger(__name__)

def ingest_directory(docs_dir:str="./data/docs"):
    """Load all .txt/.md files, split them, embed them, persist them.
    Returns the number of chunks ingested.
    """
    paths = list(Path(docs_dir).glob("*.txt")) + list(Path(docs_dir).glob("*.md"))

    if not paths:
        logger.warning("no_documents_found", dir=docs_dir)
        return 0
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    all_chunks = []
    for path in paths:
        loader = TextLoader(path)
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        all_chunks.extend(chunks)
    
    store = get_vectorstore()
    store.add_documents(all_chunks)
    logger.info("ingestion_complete", files=len(paths), chunks=len(all_chunks))
    return len(all_chunks)
    
if __name__ =="__main__":
    ingest_directory()