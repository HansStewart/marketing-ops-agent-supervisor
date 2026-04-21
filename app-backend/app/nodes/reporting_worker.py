def reporting_worker(state):
    draft = state.get("draft_output", {})
    summary = {
        "request_type": state.get("request_type"),
        "steps_executed": len(state.get("plan", [])),
        "hubspot_actions_count": len(state.get("hubspot_actions", [])),
        "status": "prepared",
    }
    draft["report_summary"] = summary

    logs = state.get("logs", [])
    logs.append("Reporting summary generated")

    return {"draft_output": draft, "logs": logs}