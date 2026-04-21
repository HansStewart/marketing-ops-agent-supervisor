from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_run_endpoint_lead_intake():
    payload = {
        "request": "Qualify this inbound lead, create the CRM record, and recommend the next best follow-up action.",
        "business_context": {
            "company_name": "PRX Optimize Solutions",
            "industry": "Marketing & Technology",
            "primary_offer": "Optimize dashboards, projects, and workflows",
            "target_audience": "Small to medium size digital product companies",
            "tool_stack": "HubSpot, Slack",
            "workflow_goal": "Reduce manual intake and handoff time by qualifying inbound requests, updating HubSpot records, notifying the team in Slack, and routing the next best operational action."
        }
    }

    response = client.post("/run", json=payload)
    assert response.status_code == 200

    data = response.json()

    assert data["request_type"] == "lead_intake"
    assert "plan" in data
    assert len(data["plan"]) >= 3
    assert "draft_output" in data
    assert "PRX Optimize Solutions" in data["draft_output"]["content"]
    assert "HubSpot, Slack" in data["draft_output"]["content"]
    assert data["eval_result"]["approval_required"] is True