Marketing Ops Agent Supervisor

A supervised multi-route marketing operations system that classifies requests, routes them to the correct specialist worker, and returns structured execution plans, diagnostics, copy frameworks, campaign strategies, and research briefs from one operator console.
by Hans Stewart  ·  hansstewart.dev
Architecture  ·  Portfolio  ·  GitHub

What It Does

Classifies a business request into the correct specialist route and returns a structured result designed for review, approval, and operational follow-through.
The system combines deterministic routing, route-specific workers, structured fallbacks, and a final review layer so the output is consistent even when a live language-model call is unavailable.
The result is a practical supervised agent interface for marketing operations work rather than a one-shot chatbot response.
Design pattern: deterministic routing plus specialist workers consistently produces clearer, safer outputs than a single undifferentiated prompt.
Control model: high-risk operational requests are flagged for approval instead of being executed automatically.
Use cases: CRM workflow planning, reporting diagnostics, copy generation, campaign planning, research briefs, and supervised business operations support.

How It Uses Claude, Anthropic, LangSmith, LangChain, and LangGraph

Claude via Anthropic
The copy and campaign_strategy routes use Claude through the Anthropic API to generate structured JSON outputs for marketing copy and campaign planning. These routes are designed to attempt live model generation first and then gracefully fall back to deterministic structured frameworks if the model is unavailable, the model name is invalid, or the API call fails.

Anthropic API
The backend uses the Anthropic Python SDK to call Claude directly. The app sends a system prompt and user prompt, requests JSON-only output, validates the response against Pydantic models, and returns the validated result to the frontend. This keeps copy and campaign outputs structured and renderable inside the operator console.

LangSmith
LangSmith is used for tracing and observability. Worker functions and the main supervisor run are decorated so route execution can be traced when a LangSmith API key is present. This makes it possible to inspect route selection, worker behavior, and run-level execution details during debugging and evaluation.

LangChain
LangChain is part of the project stack and supports the broader architecture around model-driven business workflows. In this supervisor, the core live model path currently calls Anthropic directly for strict JSON handling, but the project environment includes LangChain so the system can be extended into richer prompt chains, reusable model abstractions, and tool-driven workflows as the product evolves.

LangGraph
LangGraph is included as part of the orchestration stack for graph-based agent design and future expansion into more explicit stateful workflow routing. The current supervisor already behaves like a routed graph at the product level: intake, decisioning, specialist worker dispatch, review shaping, and frontend delivery. LangGraph support in the environment makes it straightforward to evolve this deterministic supervisor into a deeper state-machine or graph-executed multi-agent workflow.

Backend Workflow

Step 1 — Request intake
Input: Business request plus optional business context
Receives a request through the API and accepts structured context such as company, industry, offer, target audience, tool stack, and workflow goal. Prepares the run state that the supervisor uses across the route selection and worker execution flow.

Step 2 — Deterministic route classification
Intermediate: Route decision object
Evaluates the request against a route table and classifies it into one of seven routes: crm_ops, reporting, copy, campaign_strategy, research, clarify, or reject. Assigns confidence, risk level, missing inputs, and approval requirements before worker execution begins.

Step 3 — Specialist worker execution
Processing: Route-specific structured generation
Dispatches the request to the correct worker. CRM ops returns workflow blueprints and QA checklists. Reporting returns diagnostic frameworks and KPI investigation paths. Copy and campaign strategy attempt live Claude generation through Anthropic and fall back to structured frameworks when needed. Research returns positioning and market-analysis briefs. Clarify and reject keep the system safe when a request is ambiguous or operationally risky.

Step 4 — Final review shaping
Processing: Standardized response assembly
Wraps the worker output into a consistent response shape with decision metadata, route used, next step guidance, and a deliverable payload. Keeps frontend rendering predictable regardless of which route was selected.

Step 5 — Frontend delivery
Output: Supervised agent result
Displays the routing decision, confidence, risk status, approval state, structured output, and raw JSON trace inside a React operator console. Supports review, debugging, and presentation from a single UI.

System Routes

RoutePurpose
crm_opsCRM workflow blueprints, routing logic, lifecycle-stage handling, SLA checks, notifications, and implementation planning
reportingKPI analysis, funnel diagnostics, attribution review, performance troubleshooting, and investigation frameworks
copyStructured copy outputs such as nurture sequences, outreach, landing page copy, and conversion messaging
campaign_strategyGo-to-market planning, ICP definition, channel strategy, positioning, campaign sequencing, and success metrics
researchMarket landscape, competitor framing, persona research, positioning analysis, and open-question briefs
clarifyClarifying questions when the request is too vague to route safely
rejectSafe refusal for risky direct execution requests such as live CRM changes or immediate sends

Frontend Experience

The frontend provides a business-context form, request intake, scenario shortcuts, execution graph, route decision display, structured route output, and raw JSON inspection.
The interface is designed for supervised operations work, not autonomous live execution.
High-risk routes can surface approval requirements before operational follow-through.
Fallback behavior for copy and campaign strategy is preserved so the product remains usable even when the live model is unavailable.

Tech Stack

LayerTechnology
LanguagePython 3.11
Backend FrameworkFastAPI
FrontendReact with TypeScript
ServerUvicorn
AI ModelClaude via Anthropic
TracingLangSmith
AI FrameworkLangChain
Agent Graph LayerLangGraph
DeploymentGoogle Cloud Run for backend, static frontend deployment for UI
ArchitectureDeterministic router plus specialist workers

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

Frontend
http://localhost:3000

Backend health
http://127.0.0.1:8000/health

Backend docs
http://127.0.0.1:8000/docs

Environment Variables

VariableRequiredPurpose
ANTHROPIC_API_KEYOptional for fallback mode, required for live Claude generationAnthropic API access for copy and campaign routes
ANTHROPIC_MODELRecommendedClaude model selection for copy and campaign routes
ANTHROPIC_TIMEOUT_SECONDSOptionalRequest timeout control for Anthropic calls
ANTHROPIC_MAX_RETRIESOptionalRetry count for Anthropic calls
LANGSMITH_API_KEYOptionalTracing and observability for route runs

Example Request Types

CRM Ops
Build a HubSpot workflow for MQL to SQL handoff using round robin assignment with a fallback owner and 2-hour SLA check.

Reporting
Analyze why booked calls dropped from paid search leads last month.

Copy
Write a 5-email nurture sequence for inbound leads from paid search who did not book a call.

Campaign Strategy
Create a go-to-market campaign plan for a new SMB offer targeting roofing contractors.

Research
Research how the top 3 HubSpot competitors position their CRM automation for SMBs.

Deployment

Recommended production deployment pattern:

Backend
Deploy app-backend to Google Cloud Run.

Frontend
Deploy app-frontend as a static frontend and point its API base URL to the Cloud Run backend URL.

This keeps the backend scalable and the frontend simple to update.

GitHub Workflow

git add .
git commit -m "Finish MVP for marketing ops agent supervisor"
git push origin main

If the repository is brand new, create the empty GitHub repository first, then connect the local repo as origin and push.

Why This Project Exists

Marketing and ops teams often need structured planning, diagnostics, and execution guidance, but most AI interfaces collapse everything into one generic answer.
This project separates request types into specialist paths, preserves a consistent response contract, and keeps risky operations supervised rather than automatic.
It is designed to function as an operator console for AI-assisted marketing operations work.

Full Agent Ecosystem

AgentRepository
Website Audit Agentgithub.com/HansStewart/website-audit-agent
AI Content Pipelinegithub.com/HansStewart/ai-content-pipeline
Voice-to-CRM Agentgithub.com/HansStewart/voice-to-crm
Pipeline Intelligence Agentgithub.com/HansStewart/pipeline-intelligence-agent
CRM Automation Agentgithub.com/HansStewart/crm-agent
AI Data Agentgithub.com/HansStewart/ai-data-agent
RAG Document Intelligencegithub.com/HansStewart/rag-agent
AI Architecturehansstewart.github.io/ai-architecture

Hans Stewart  ·  Marketing Automation Engineer  ·  hansstewart.dev
