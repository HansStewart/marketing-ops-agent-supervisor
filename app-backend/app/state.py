from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict, total=False):
    request_id: str
    user_input: str
    request_type: str
    plan: List[Dict[str, Any]]
    hubspot_actions: List[Dict[str, Any]]
    draft_output: Dict[str, Any]
    eval_result: Dict[str, Any]
    approval_required: bool
    approved: bool
    final_result: Dict[str, Any]
    logs: List[str]
    synthetic_context: Dict[str, Any]