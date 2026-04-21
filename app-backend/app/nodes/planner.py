from app.services.llm import llm
from app.schemas import PlanOutput

def planner_node(state):
    structured = llm.with_structured_output(PlanOutput)
    result = structured.invoke(
        f"Create a 3-step marketing ops execution plan.\n"
        f"Request type: {state.get('request_type')}\n"
        f"Request: {state.get('user_input')}\n"
        f"Workers available: hubspot_worker, content_worker, reporting_worker"
    )
    logs = state.get("logs", [])
    logs.append("Plan created")
    return {
        "plan": [step.model_dump() for step in result.steps],
        "logs": logs,
    }