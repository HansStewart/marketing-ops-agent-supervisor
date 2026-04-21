def approval_gate(state):
    if state.get("approval_required", True):
        return {
            "approved": False,
            "final_result": {
                "status": "pending_approval",
                "message": "Human approval required before finalizing.",
            },
        }
    return {"approved": True}