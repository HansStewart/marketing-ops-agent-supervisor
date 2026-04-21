def hubspot_worker(state):
    logs = state.get("logs", [])
    actions = state.get("hubspot_actions", [])

    if state.get("request_type") == "lead_intake":
        fake_contact = {
            "id": "demo-contact-001",
            "properties": {
                "email": "new.lead@example.com",
                "firstname": "Taylor",
                "lastname": "Brooks",
                "company": "Apex Growth",
            },
        }
        fake_deal = {
            "id": "demo-deal-001",
            "properties": {
                "dealname": "Apex Growth - New Opportunity",
                "amount": "12000",
                "pipeline": "default",
                "dealstage": "appointmentscheduled",
            },
        }
        actions.append({"contact": fake_contact, "deal": fake_deal})
        logs.append("Simulated HubSpot contact and deal created.")

    return {
        "hubspot_actions": actions,
        "logs": logs,
    }