Marketing Ops Agent Supervisor

A supervised multi-route marketing operations system built on Claude, LangChain, LangGraph, and LangSmith that classifies requests, routes them to the correct specialist worker, and returns structured execution plans, diagnostics, copy frameworks, campaign strategies, and research briefs from one operator console.

By Hans Stewart
hansstewart.dev
Portfolio: hansstewart.dev
GitHub: github.com/HansStewart

Live App:
https://marketing-ops-agent-1075083906427.us-central1.run.app



What It Does

Classifies a business request into the correct specialist route and returns a structured result designed for review, approval, and operational follow-through. The system combines deterministic routing, route-specific workers, structured fallbacks, and a final review layer so the output is consistent even when a live model call is unavailable.

The result is a practical supervised agent interface for marketing operations work rather than a one-shot chatbot response.

Design pattern:
Deterministic routing plus specialist workers consistently produces clearer, safer outputs than a single undifferentiated prompt.

Control model:
High-risk operational requests are flagged for approval instead of being executed automatically.

Use cases:
CRM workflow planning
Reporting diagnostics
Copy generation
Campaign planning
Research briefs
Supervised business operations support

AI Stack

Claude

Claude powers live generation in this supervisor. The copy and campaign_strategy routes call Claude through the Anthropic SDK, which sends a structured system prompt and user prompt, requests JSON output, and validates the response before it reaches the frontend. When Claude is unavailable, both routes fall back to deterministic structured frameworks rather than failing silently, so the operator always receives a usable result.

LangChain

LangChain provides the AI application framework layer. It supports the model workflow architecture and makes it straightforward to extend the supervisor with reusable prompt abstractions, model wrappers, and tool integrations as the product grows.

LangGraph

LangGraph provides the graph orchestration layer. The supervisor already follows a graph-shaped execution model: request intake, route decision, worker dispatch, review shaping, and frontend delivery. LangGraph gives that model an explicit stateful foundation for evolving into deeper branching, guarded transitions, and multi-agent graph workflows.

LangSmith

LangSmith provides tracing and observability across the full run. Supervisor execution and worker functions are traced so route selection, worker behavior, and run-level decisions can be inspected, evaluated, and debugged.

Backend Workflow

Step 1 — Request intake

Input:
Business request plus optional business context

Receives a request through the API alongside structured context such as company name, industry, offer, target audience, tool stack, and workflow goal. Prepares the run state used across the entire supervisor flow.

Step 2 — Deterministic route classification

Intermediate:
Route decision object

Evaluates the request against a route table and classifies it into one of seven routes:
crm_ops
reporting
copy
campaign_strategy
research
clarify
reject

Assigns confidence, risk level, missing inputs, and approval requirements before any worker runs.

Step 3 — Specialist worker execution

Processing:
Route-specific structured generation

Dispatches the request to the correct worker.

CRM ops returns workflow blueprints and QA checklists.

Reporting returns diagnostic frameworks and KPI investigation paths.

Copy and campaign strategy route through Claude via Anthropic and fall back to structured frameworks when the model is unavailable.

Research returns positioning and market-analysis briefs.

Clarify and reject keep the system safe when a request is ambiguous or operationally risky.

Step 4 — Final review shaping

Processing:
Standardized response assembly

Wraps the worker output into a consistent response shape with decision metadata, route used, next step guidance, and a deliverable payload. Keeps frontend rendering predictable regardless of which route was selected.

Step 5 — Frontend delivery

Output:
Supervised agent result

Displays the routing decision, confidence, risk status, approval state, structured output, and raw JSON trace inside a React operator console. Supports review, debugging, and presentation from a single UI.

System Routes

crm_ops
Purpose: CRM workflow blueprints, routing logic, lifecycle-stage handling, SLA checks, notifications, and implementation planning

reporting
Purpose: KPI analysis, funnel diagnostics, attribution review, performance troubleshooting, and investigation frameworks

copy
Purpose: Claude-powered structured copy generation with deterministic fallback support

campaign_strategy
Purpose: Claude-powered campaign planning with deterministic fallback support

research
Purpose: Market landscape, competitor framing, persona research, positioning analysis, and open-question briefs

clarify
Purpose: Clarifying questions when the request is too vague to route safely

reject
Purpose: Safe refusal for risky direct execution requests such as live CRM changes or immediate sends

Frontend Experience

The frontend provides a business-context form, request intake, scenario shortcuts, execution graph, route decision display, structured route output, and raw JSON inspection.

The interface is designed for supervised operations work, not autonomous live execution.

High-risk routes surface approval requirements before operational follow-through.

Fallback behavior on Claude-powered routes is preserved so the product remains usable even when the live model is unavailable.

Tech Stack

Primary AI model:
Claude

AI provider:
Anthropic

AI application framework:
LangChain

Graph orchestration layer:
LangGraph

Tracing and observability:
LangSmith

Language:
Python 3.11

Backend framework:
FastAPI

Frontend:
React with TypeScript

Server:
Uvicorn

Deployment:
Google Cloud Run

Local Development

Clone the repository:

git clone https://github.com/HansStewart/marketing-ops-agent-supervisor.git
cd marketing-ops-agent-supervisor

Run the backend:

cd app-backend
pip install -r requirements.txt
uvicorn main:app --reload

Run the frontend in a second terminal:

cd app-frontend
npm install
npm start

Local URLs

Frontend:
http://localhost:3000

Backend health:
http://127.0.0.1:8000/health

Backend docs:
http://127.0.0.1:8000/docs

Environment Variables

ANTHROPIC_API_KEY
Required for live Claude generation
Used for Anthropic API access for copy and campaign routes

ANTHROPIC_MODEL
Recommended
Used for Claude model selection for copy and campaign routes

ANTHROPIC_TIMEOUT_SECONDS
Optional
Used for request timeout control for Anthropic calls

ANTHROPIC_MAX_RETRIES
Optional
Used for retry count for Anthropic calls

LANGSMITH_API_KEY
Optional
Used for tracing and observability for route runs

Example Request Types

CRM Ops

Build a HubSpot workflow for MQL to SQL handoff using round robin assignment with a fallback owner and a 2-hour SLA check.

Reporting

Analyze why booked calls dropped from paid search leads last month.

Copy

Write a 5-email nurture sequence for inbound leads from paid search who did not book a call.

Campaign Strategy

Create a go-to-market campaign plan for a new SMB offer targeting roofing contractors.

Research

Research how the top 3 HubSpot competitors position their CRM automation for SMBs.

Deployment

Backend and Frontend

Deploy the FastAPI backend to Google Cloud Run and serve the built React frontend from the same container.

Production URL:
https://marketing-ops-agent-1075083906427.us-central1.run.app

Health Check:
https://marketing-ops-agent-1075083906427.us-central1.run.app/health

Docs:
https://marketing-ops-agent-1075083906427.us-central1.run.app/docs

GitHub Workflow

git add README.md
git commit -m "Update README with production Cloud Run URL"
git push origin main

Why This Project Exists

Marketing and ops teams often need structured planning, diagnostics, and execution guidance, but most AI interfaces collapse everything into one generic answer.

This project separates request types into specialist paths, preserves a consistent response contract, and keeps risky operations supervised rather than automatic.

It is designed to function as an operator console for AI-assisted marketing operations work.

Full Agent Ecosystem

Website Audit Agent
github.com/HansStewart/website-audit-agent

AI Content Pipeline
github.com/HansStewart/ai-content-pipeline

Voice-to-CRM Agent
github.com/HansStewart/voice-to-crm

Pipeline Intelligence Agent
github.com/HansStewart/pipeline-intelligence-agent

CRM Automation Agent
github.com/HansStewart/crm-agent

AI Data Agent
github.com/HansStewart/ai-data-agent

RAG Document Intelligence
github.com/HansStewart/rag-agent

AI Architecture
hansstewart.github.io/ai-architecture

Hans Stewart
Marketing Automation Engineer
hansstewart.dev