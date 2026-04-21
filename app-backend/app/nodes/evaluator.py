from app.services.llm import llm
from app.schemas import EvalOutput

def evaluator_node(state):
    structured = llm.with_structured_output(EvalOutput)
    result = structured.invoke(
        f"Evaluate this marketing ops output for completeness and clarity.\n"
        f"Request type: {state.get('request_type')}\n"
        f"Output: {state.get('draft_output')}\n\n"
        f"Set approval_required=true if CRM changes occurred or confidence is below 85.\n"
        f"Score 0-100."
    )
    logs = state.get("logs", [])
    logs.append(f"Eval: {result.pass_fail} | Score: {result.score}")
    return {
        "eval_result": result.model_dump(),
        "approval_required": result.approval_required,
        "logs": logs,
    }