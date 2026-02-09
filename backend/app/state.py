from typing import TypedDict, List, Dict, Optional, Any

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired

class AgentState(TypedDict):
    """
    Shared state for the VeriFlow LangGraph workflow.
    """
    # Metadata
    run_id: Optional[str]               # Unique ID for this execution run
    
    # Inputs
    pdf_path: str
    repo_path: str
    user_context: Optional[str]         # Global user context provided at start
    
    # Step 1: Scholar Output
    isa_json: Optional[Dict[str, Any]]  # The extracted ISA model
    
    # Step 2: Engineer Context & Output
    repo_context: Optional[str]         # Summary of files in the repo
    generated_code: Optional[Dict[str, Any]]  # Keys: 'dockerfile', 'cwl', 'airflow_dag'
    
    # Validation & Self-Healing
    validation_errors: List[str]
    validation_report: NotRequired[Dict[str, Any]]
    retry_count: int
    client_id: Optional[str] # For WebSocket updates
    
    # Step 3: Reviewer Output
    review_decision: Optional[str]      # 'approved' or 'rejected'
    review_feedback: Optional[str]

    # --- Plan & Apply Pattern ---
    # Stores specific user instructions for each agent to be applied on restart
    agent_directives: Dict[str, str]