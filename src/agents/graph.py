from langgraph.graph import END, StateGraph
from src.agents.state import AgentState
from src.agents.researcher import researcher_node
from src.agents.critic import critic_node
from src.agents.hitl import human_review_node
from langgraph.checkpoint.memory import MemorySaver

def should_retry(state:AgentState):
    if state["critic_passed"]:
        return "Passed"
    if state["retry_count"]>=state["max_retries"]:
        return "max_retries_reached"
    return "retry"

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("researcher",researcher_node)
    builder.add_node("critic",critic_node)
    builder.add_node("human_interrupt",human_review_node)
    builder.set_entry_point("researcher")
    builder.add_edge("researcher","critic")
    builder.add_conditional_edges(
        "crictic",
        should_retry,
        {
        "retry":"researcher",
        "passed":"human_interrupt",
        "max_retries_reached":"human_interrupt"
        }
    )
    builder.add_edge("human_interrupt",END)
    check_pointer = MemorySaver()
    return builder.compile(checkpointer=)

    
