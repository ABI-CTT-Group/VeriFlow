from typing import Literal

from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.graph.nodes import (
    scholar_node,
    engineer_node,
    validate_node,
    reviewer_node
)

# --- Conditional Logic ---

def decide_next_step(state: AgentState) -> Literal["engineer", "reviewer"]:
    """
    Self-Healing Logic:
    - If validation errors exist and we haven't hit the retry limit (3), go back to Engineer.
    - If validation errors exist but we hit the limit, go to Reviewer (to fail/critique).
    - If no errors, go to Reviewer (to approve).
    """
    errors = state.get("validation_errors", [])
    retry_count = state.get("retry_count", 0)
    MAX_RETRIES = 3
    
    if errors:
        if retry_count < MAX_RETRIES:
            return "engineer"
        else:
            return "reviewer" # Fail path
    
    return "reviewer" # Success path

# --- Graph Construction ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("scholar", scholar_node)
workflow.add_node("engineer", engineer_node)
workflow.add_node("validate", validate_node)
workflow.add_node("reviewer", reviewer_node)

# Set Entry Point
workflow.set_entry_point("scholar")

# Add Edges
# 1. Scholar always feeds into Engineer
workflow.add_edge("scholar", "engineer")

# 2. Engineer always feeds into Validate
workflow.add_edge("engineer", "validate")

# 3. Validate branches based on errors/retries
workflow.add_conditional_edges(
    "validate",
    decide_next_step,
    {
        "engineer": "engineer",
        "reviewer": "reviewer"
    }
)

# 4. Reviewer is the terminal node (Decision recorded in state)
workflow.add_edge("reviewer", END)

# Compile Graph
app_graph = workflow.compile()