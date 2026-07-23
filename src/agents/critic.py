from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.core.llm import get_llm
from src.agents.state import AgentState
from src.observability.logging_config import get_logger
from src.rag.retriever import format_context

logger = get_logger(__name__)

CRITIC_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a strict quality reviewer. Evaluate the draft answer against "
               "the question and context. Respond ONLY with JSON: "
               '{{"passed": true/false, "feedback": "specific, actionable feedback"}}. '
               "Fail answers that are vague, unsupported by context, or don't address "
               "the question directly."),
    ("human", "Question: {question}\n\nContext:\n{context}\n\nDraft Answer:\n{draft}"),
]) 

async def critic_node(state:AgentState):
    chain = CRITIC_PROMPT|get_llm(temperature=0.2)|JsonOutputParser()
    result = chain.invoke({
        "question": state["question"],
        "context": format_context(state["retrieved_docs"]),
        "draft": state["draft_answer"],
    })

    logger.info("critic_evaluated", passed=result["passed"], retry_count=state.get("retry_count", 0))
    return {
        "critic_passed": result["passed"],
        "critic_feedback": result["feedback"],
        "retry_count": state.get("retry_count", 0) + 1,
    }
