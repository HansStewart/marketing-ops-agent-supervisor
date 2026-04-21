Marketing Ops Agent Supervisor
=============================

Overview
--------

Marketing Ops Agent Supervisor is a two-part application that classifies a marketing or operations request, routes it to the correct specialist worker, and returns a structured response for review.

The backend is a FastAPI service that handles request routing, worker execution, fallback behavior, and final response shaping.

The frontend is a React and TypeScript application that lets a user enter business context, submit a request, inspect the route decision, review structured output, and view raw JSON for debugging.

This project is built for supervised execution. It can recommend workflows, reporting diagnostics, campaign plans, copy frameworks, and research briefs, but it should not make risky live operational changes automatically.

Current routes
--------------

The supervisor supports these routes:

crm_ops
reporting
copy
campaign_strategy
research
clarify
reject

What each route does
--------------------

crm_ops
Returns a structured workflow blueprint for CRM and automation tasks such as lead routing, lifecycle updates, assignment logic, notifications, and SLA checks.

reporting
Returns a structured reporting or diagnostic framework for KPI analysis, funnel analysis, attribution review, and performance investigation.

copy
Attempts to generate structured marketing copy through Anthropic. If the Anthropic call fails, the app falls back to a safe structured copy framework.

campaign_strategy
Attempts to generate a structured campaign plan through Anthropic. If the Anthropic call fails, the app falls back to a safe structured campaign framework.

research
Returns a structured research brief covering market context, competitor framing, open questions, implications, and recommended next steps.

clarify
Returns clarifying questions when the request is too vague to route with confidence.

reject
Rejects risky direct execution requests and offers a safer planning alternative.

Project structure
-----------------

marketing-ops-agent-supervisor/
app-backend/
app-frontend/

Backend summary
---------------

The backend uses FastAPI and includes:

A route_request function for deterministic classification
Worker functions for each supported route
Structured fallback behavior for copy and campaign strategy
A review_result function that standardizes the final response shape
A /run endpoint that accepts the request and business context
A /health endpoint for quick health checks

Frontend summary
----------------

The frontend uses React and TypeScript and includes:

A request form
Business context inputs
Route badges and confidence display
Structured route output rendering
A decision trace view with raw JSON toggle
A CRM-focused output view for crm_ops runs
An approval state for high-risk routes

Request and response shape
--------------------------

The frontend sends a POST request to /run with this general shape:

{
  "input": "Build a HubSpot workflow for inbound lead routing",
  "business_context": {
    "company_name": "Stewart Strategy Suite",
    "industry": "Marketing automation / AI consulting",
    "primary_offer": "AI implementation and marketing ops consulting",
    "target_audience": "SMB founders and revenue teams",
    "tool_stack": "HubSpot, FastAPI, React, LangChain",
    "workflow_goal": "Improve lead routing and campaign execution"
  }
}

The backend returns this general shape:

{
  "decision": {
    "route": "crm_ops",
    "confidence": 0.95,
    "reason": "Request is about CRM, workflows, or automation.",
    "missing_inputs": [],
    "risk_level": "high",
    "requires_human_approval": true
  },
  "result": {
    "route_used": "crm_ops",
    "deliverable": {},
    "next_step": "Review the output and refine the request if you want a more specific deliverable.",
    "max_steps": 6
  }
}

Running locally
---------------

Backend

1. Open a terminal.
2. Change into the backend folder.
3. Activate the virtual environment if you are using one.
4. Start the FastAPI app.

Commands:

cd app-backend
uvicorn main:app --reload

Frontend

1. Open a second terminal.
2. Change into the frontend folder.
3. Start the React development server.

Commands:

cd app-frontend
npm start

Local URLs
----------

Frontend:
http://localhost:3000

Backend health:
http://127.0.0.1:8000/health

Backend docs:
http://127.0.0.1:8000/docs

Environment variables
---------------------

Recommended backend environment variables:

ANTHROPIC_API_KEY
ANTHROPIC_MODEL
ANTHROPIC_TIMEOUT_SECONDS
ANTHROPIC_MAX_RETRIES
LANGSMITH_API_KEY

Important note about Anthropic behavior
---------------------------------------

The copy and campaign_strategy routes are designed to fall back gracefully if the Anthropic request fails. This means the app remains usable even if the API key is missing, the model name is unavailable, or the request fails for another reason.

If a fallback is triggered, the UI should show a polished framework response without exposing a raw provider error message to the end user.

Recommended test prompts
------------------------

reporting
Reporting - analyze why booked calls dropped from paid search leads last month.

crm_ops
Build a HubSpot workflow for MQL to SQL handoff using round robin assignment with a fallback owner and 2-hour SLA check.

copy
Write a 5-email nurture sequence for inbound leads from paid search who did not book a call.

campaign_strategy
Create a go-to-market campaign plan for a new SMB offer targeting roofing contractors.

research
Research how the top 3 HubSpot competitors position their CRM automation for SMBs.

clarify
Help me improve marketing.

reject
Update HubSpot and send this email to all leads right now.

Deployment approach
-------------------

Recommended production deployment:

Backend
Deploy app-backend to Google Cloud Run as a containerized FastAPI service.

Frontend
Either deploy app-frontend separately as a static site, or build it and host it behind a simple static hosting setup.

If you want a single public product link quickly, the simplest production path is:

1. Deploy the backend to Cloud Run.
2. Deploy the frontend to a static host.
3. Point the frontend API base URL to the Cloud Run backend URL.

GitHub workflow
---------------

A simple Git workflow for this project:

git status
git add .
git commit -m "Finish MVP wiring for marketing ops agent supervisor"
git push origin master

If your default branch is main instead of master, replace master with main.

What finished looks like
------------------------

This MVP is considered complete when:

The frontend loads without TypeScript errors
The backend responds successfully on /health and /run
Each route classifies correctly
Each route renders the expected structured output
High-risk routes show approval behavior
Copy and campaign routes fall back gracefully when the LLM is unavailable
The raw provider error is hidden from the end user interface

Next improvements
-----------------

Useful next upgrades after MVP:

Split App.tsx into smaller components
Add persistent run history
Add authentication
Add better route evaluation logging
Add Cloud Run deployment files if not already present
Add frontend environment configuration for production API URLs
