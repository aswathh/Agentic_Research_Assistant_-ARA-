from typing import TypedDict, Annotated
from langchain_core.documents import Document
import operators

class AgentState(TypedDict):
    question: str
    retrieved_docs: list[Document]
    tool_results: Annotated[list[str], operator.add]
    draft_answer: str
    critic_feedback: str
    critic_passed: bool
    retry_count: int
    max_retries: int
    final_answer: str