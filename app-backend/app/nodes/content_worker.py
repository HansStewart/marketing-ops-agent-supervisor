from app.services.llm import llm

def content_worker(state):
    request_type = state.get("request_type")
    user_input = state.get("user_input")
    context = state.get("synthetic_context", {})
    company = context.get("company", {})
    leads = context.get("sample_leads", [])
    lead = leads[0] if leads else {"firstname": "Taylor", "lastname": "Brooks", "company": "Apex Growth", "email": "new.lead@example.com"}

    type_instructions = {
        "campaign_brief": (
            f"Write a campaign brief for {company.get('name', 'the company')} ({company.get('industry', 'B2B')}).\n"
            f"Include: objective, target audience ({', '.join(company.get('target_personas', []))}), core message, CTA, 5-item launch checklist."
        ),
        "lead_intake": (
            f"Write a lead intake summary for: {lead.get('firstname')} {lead.get('lastname')} at {lead.get('company')} ({lead.get('email')}).\n"
            f"This is an inbound lead for {company.get('name', 'the company')} in {company.get('industry', 'B2B')}.\n"
            f"Include: 2-sentence summary, 3 qualification notes, recommended next action with timeline."
        ),
        "record_audit": (
            f"Audit the lead record for {lead.get('firstname')} {lead.get('lastname')} at {lead.get('company')}.\n"
            f"Include: key findings, missing fields, top 3 cleanup recommendations."
        ),
    }

    instruction = type_instructions.get(request_type, "Summarize the marketing ops request concisely.")

    prompt = (
        f"You are a senior marketing ops specialist. Be concise and specific.\n\n"
        f"{instruction}\n\n"
        f"User request context: {user_input}"
    )

    result = llm.invoke(prompt)
    draft = state.get("draft_output", {})
    draft["content"] = result.content
    logs = state.get("logs", [])
    logs.append("Content generated")
    return {"draft_output": draft, "logs": logs}