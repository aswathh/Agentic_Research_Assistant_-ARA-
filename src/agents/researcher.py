from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.agents.state import AgentState
from src.mcp.client import call_tools
from src.rag.retriever import retrieve, format_context
import asyncio
from src.observability.logging_config import get_logger

logger = get_logger(__name__)

RESEARCHER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a careful research assistant. Answer using the provided "
               "context and tool results. If context is insufficient, say so explicitly "
               "rather than guessing. If you're given critic feedback from a previous "
               "attempt, address it directly."),
    ("human", "Question: {question}\n\nRAG Context:\n{context}\n\n"
              "Tool Results:\n{tool_results}\n\n"
              "Previous feedback (if any): {feedback}\n\n"
              "Write your answer."),
])

async def researcher_node(state: AgentState):
    docs = retrieve(state["question"])
    context = format_context(docs)

    tool_results = state.get("tool_results", [])
    if len(docs)<2:
        search_result= await call_tools("web_search", {"query": state["question"], "max_results": 2})
        tool_results = [search_result]
        
    chain = RESEARCHER_PROMPT | get_llm(temperature=0.2)
    response = chain.invoke({
        "question": state["question"],
        "context": context,
        "tool_results": "\n".join(tool_results) if tool_results else "None",
        "feedback": state.get("critic_feedback", "None — this is the first attempt"),
    })

    logger.info("researcher_draft_created", retry_count=state.get("retry_count", 0))
    return {
        "retrieved_docs": docs,
        "tool_results": tool_results,
        "draft_answer": response.content,
    }
