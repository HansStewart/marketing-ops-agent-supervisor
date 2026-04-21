def action_node(state):
    return {
        "final_result": {
            "status": "completed",
            "request_type": state.get("request_type"),
            "draft_output": state.get("draft_output"),
            "eval_result": state.get("eval_result"),
            "hubspot_actions": state.get("hubspot_actions", []),
        }
    }