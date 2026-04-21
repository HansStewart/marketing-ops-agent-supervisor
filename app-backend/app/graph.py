from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.nodes.intake_router import intake_router
from app.nodes.planner import planner_node
from app.nodes.hubspot_worker import hubspot_worker
from app.nodes.content_worker import content_worker
from app.nodes.reporting_worker import reporting_worker
from app.nodes.evaluator import evaluator_node
from app.nodes.approval_gate import approval_gate
from app.nodes.action_node import action_node

def route_after_eval(state: AgentState):
    if state.get("approval_required"):
        return "approval_gate"
    return "action_node"

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("intake_router", intake_router)
    graph.add_node("planner", planner_node)
    graph.add_node("hubspot_worker", hubspot_worker)
    graph.add_node("content_worker", content_worker)
    graph.add_node("reporting_worker", reporting_worker)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("approval_gate", approval_gate)
    graph.add_node("action_node", action_node)

    graph.add_edge(START, "intake_router")
    graph.add_edge("intake_router", "planner")
    graph.add_edge("planner", "hubspot_worker")
    graph.add_edge("hubspot_worker", "content_worker")
    graph.add_edge("content_worker", "reporting_worker")
    graph.add_edge("reporting_worker", "evaluator")

    graph.add_conditional_edges(
        "evaluator",
        route_after_eval,
        {
            "approval_gate": "approval_gate",
            "action_node": "action_node",
        },
    )

    graph.add_edge("approval_gate", END)
    graph.add_edge("action_node", END)

    return graph.compile()