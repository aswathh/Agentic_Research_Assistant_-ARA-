# Human in the loop :
from langgraph.types import interrupt
from src.observability.logging_config import get_logger
from src.agents.state import AgentState

logger = get_logger(__name__)

def human_review_node(state:AgentState):
    """Pauses the graph and surfaces the draft for human approval.
    Resumes here once a human decision is injected via Command(resume=...).
    """
    decision_payload= interrupt({
        "question": state["question"],
        "draft_answer": state["draft_answer"],
        "critic_passed": state["critic_passed"],
        "critic_feedback": state.get("critic_feedback", ""),
        "retry_count": state["retry_count"],
    })

    logger.info("Human decision recieved",decision=decision_payload.get("decision"))
    decision = decision_payload.get("decision","approve")
    if decision == "edit":
        final= decision_payload.get("edited answer",state["darft_answer"])
    elif decision == "reject":
        final = "REJECTED: this answer did not receive human approval."
    else :
        final = state["darft_answer"]
    
    return{
        "decision":decision,
        "final_answer":final,
    }
    

    
