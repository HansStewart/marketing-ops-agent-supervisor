from app.services.llm import llm
from app.schemas import IntakeRoute

def intake_router(state):
    structured = llm.with_structured_output(IntakeRoute)
    result = structured.invoke(
        f"Classify this marketing ops request into lead_intake, campaign_brief, or record_audit.\n\nRequest: {state['user_input']}"
    )
    logs = state.get("logs", [])
    logs.append(f"Routed to: {result.request_type}")
    return {
        "request_type": result.request_type,
        "logs": logs,
    }