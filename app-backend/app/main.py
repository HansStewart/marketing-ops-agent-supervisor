import os
import json
import time
from functools import lru_cache
from typing import Literal, List, Dict, Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

try:
    from pydantic_settings import BaseSettings
except ImportError:
    BaseSettings = BaseModel


load_dotenv()


# ── LangSmith tracing (no-ops gracefully if env vars not set) ──────────────
try:
    from langsmith import traceable
    TRACING_ENABLED = bool(os.getenv("LANGSMITH_API_KEY"))
except ImportError:
    def traceable(func=None, **kwargs):
        if func is not None:
            return func

        def decorator(f):
            return f
        return decorator
    TRACING_ENABLED = False


# ── Settings ────────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    anthropic_api_key: str = Field(default=os.getenv("ANTHROPIC_API_KEY", ""))
    anthropic_model: str = Field(default=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"))
    anthropic_timeout_seconds: float = Field(default=float(os.getenv("ANTHROPIC_TIMEOUT_SECONDS", "60")))
    anthropic_max_retries: int = Field(default=int(os.getenv("ANTHROPIC_MAX_RETRIES", "2")))
    app_title: str = Field(default="Marketing Ops Agent Supervisor")

    if BaseSettings is not BaseModel:
        model_config = {
            "env_file": ".env",
            "env_file_encoding": "utf-8",
            "extra": "ignore",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── Constants ──────────────────────────────────────────────────────────────
MAX_STEPS = 6


ALLOWED_ROUTES = {
    "clarify",
    "crm_ops",
    "reporting",
    "copy",
    "campaign_strategy",
    "research",
    "reject",
}


HIGH_RISK_ROUTES = {
    "crm_ops",
    "reject",
}


# ── App ────────────────────────────────────────────────────────────────────
settings = get_settings()
app = FastAPI(title=settings.app_title)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ─────────────────────────────────────────────────────────────────
class BusinessContext(BaseModel):
    company_name: str = ""
    industry: str = ""
    primary_offer: str = ""
    target_audience: str = ""
    tool_stack: str = ""
    workflow_goal: str = ""


class RunRequest(BaseModel):
    input: str
    business_context: Optional[BusinessContext] = None


class RouteDecision(BaseModel):
    route: Literal[
        "clarify",
        "crm_ops",
        "reporting",
        "copy",
        "campaign_strategy",
        "research",
        "reject",
    ] = Field(description="Best route for this request.")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    missing_inputs: List[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"]
    requires_human_approval: bool


class CopyBrief(BaseModel):
    company: str
    offer: str
    audience: str
    goal: str
    tone: str
    cta: str


class CopyFramework(BaseModel):
    problem: str
    promise: str
    proof: str
    cta: str


class SequenceOutline(BaseModel):
    sequence_type: str
    email_1: str
    email_2: str
    email_3: str
    email_4: str
    email_5: str


class CopyWorkerOutput(BaseModel):
    summary: str
    asset_type: str
    target_audience: str
    copy_brief: CopyBrief
    copy_framework: CopyFramework
    copy: str
    variants: List[str]
    sequence_outline: SequenceOutline
    notes: List[str]
    next_step: str
    original_request: str


class CampaignBusinessContextApplied(BaseModel):
    company: str
    industry: str
    offer: str
    audience: str
    goal: str


class CampaignICP(BaseModel):
    primary_audience: str
    industry_context: str
    buying_trigger: str
    pain_point: str


class CampaignPositioning(BaseModel):
    problem: str
    promise: str
    differentiator: str
    proof: str


class CampaignWorkerOutput(BaseModel):
    summary: str
    business_context_applied: CampaignBusinessContextApplied
    campaign_type: str
    objective: str
    icp: CampaignICP
    positioning: CampaignPositioning
    channels: List[str]
    campaign_plan: List[str]
    risks: List[str]
    success_metrics: List[str]
    next_step: str
    original_request: str


# ── Router ─────────────────────────────────────────────────────────────────
def route_request(user_request: str) -> RouteDecision:
    text = user_request.lower()

    reject_keywords = [
        "send email",
        "update hubspot",
        "change records",
        "edit live workflow",
        "trigger campaign now",
        "delete all crm",
        "shut off all automations",
    ]

    copy_keywords = [
        "write email",
        "email copy",
        "landing page copy",
        "copy",
        "nurture",
        "outreach",
        "cta",
        "subject line",
        "subject lines",
        "headline",
        "ad copy",
        "sales email",
        "sequence",
    ]

    campaign_keywords = [
        "campaign",
        "go-to-market",
        "gtm",
        "launch plan",
        "positioning",
        "channel strategy",
        "icp",
        "campaign plan",
        "multi-channel",
        "offer launch",
    ]

    crm_keywords = [
        "hubspot",
        "crm",
        "workflow",
        "automation",
        "pipeline",
        "lead routing",
        "lifecycle stage",
        "round robin",
        "owner assignment",
        "sla",
        "handoff",
    ]

    reporting_keywords = [
        "report",
        "dashboard",
        "kpi",
        "funnel",
        "attribution",
        "metrics",
        "analyze",
        "analysis",
        "why did",
        "why has",
        "why have",
        "diagnose",
        "performance",
    ]

    research_keywords = [
        "research",
        "competitor",
        "market",
        "persona",
        "industry",
        "benchmark",
        "compare",
    ]

    if any(word in text for word in reject_keywords):
        route = "reject"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.95,
            reason="Request asks for direct live execution or risky operational changes.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "medium",
            requires_human_approval=is_high_risk,
        )

    if any(word in text for word in copy_keywords) and not any(
        word in text for word in crm_keywords + reporting_keywords
    ):
        route = "copy"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.95,
            reason="Request is about writing marketing copy.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "low",
            requires_human_approval=is_high_risk,
        )

    if any(word in text for word in campaign_keywords) and not any(
        word in text for word in crm_keywords + reporting_keywords
    ):
        route = "campaign_strategy"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.90,
            reason="Request is about campaign or strategic planning.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "low",
            requires_human_approval=is_high_risk,
        )

    if any(word in text for word in crm_keywords):
        route = "crm_ops"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.95,
            reason="Request is about CRM, workflows, or automation.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "medium",
            requires_human_approval=is_high_risk,
        )

    if any(word in text for word in reporting_keywords):
        route = "reporting"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.95,
            reason="Request is about reporting, analysis, or performance diagnosis.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "low",
            requires_human_approval=is_high_risk,
        )

    if any(word in text for word in research_keywords):
        route = "research"
        is_high_risk = route in HIGH_RISK_ROUTES
        return RouteDecision(
            route=route,
            confidence=0.90,
            reason="Request is about research or market context.",
            missing_inputs=[],
            risk_level="high" if is_high_risk else "low",
            requires_human_approval=is_high_risk,
        )

    route = "clarify"
    is_high_risk = route in HIGH_RISK_ROUTES
    return RouteDecision(
        route=route,
        confidence=0.60,
        reason="Request is ambiguous or missing clear intent.",
        missing_inputs=[
            "Describe the exact outcome you want: CRM ops, reporting, copy, campaign strategy, or research."
        ],
        risk_level="high" if is_high_risk else "low",
        requires_human_approval=is_high_risk,
    )


# ── Context helpers ────────────────────────────────────────────────────────
def ctx_company(ctx: Optional[BusinessContext]) -> str:
    return ctx.company_name if ctx and ctx.company_name else "your company"


def ctx_industry(ctx: Optional[BusinessContext]) -> str:
    return ctx.industry if ctx and ctx.industry else "your industry"


def ctx_offer(ctx: Optional[BusinessContext]) -> str:
    return ctx.primary_offer if ctx and ctx.primary_offer else "your primary offer"


def ctx_audience(ctx: Optional[BusinessContext]) -> str:
    return ctx.target_audience if ctx and ctx.target_audience else "your target audience"


def ctx_tools(ctx: Optional[BusinessContext]) -> str:
    return ctx.tool_stack if ctx and ctx.tool_stack else "your CRM and tool stack"


def ctx_goal(ctx: Optional[BusinessContext]) -> str:
    return ctx.workflow_goal if ctx and ctx.workflow_goal else "your workflow goal"


# ── Anthropic helpers ──────────────────────────────────────────────────────
def get_anthropic_client() -> Anthropic:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return Anthropic(
        api_key=settings.anthropic_api_key,
        timeout=settings.anthropic_timeout_seconds,
    )


def extract_text_from_anthropic_response(response: Any) -> str:
    text_blocks = [block for block in response.content if getattr(block, "type", "") == "text"]
    if not text_blocks:
        raise ValueError("No text block returned from Anthropic")
    return text_blocks[0].text.strip()


def call_anthropic_json(
    *,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1400,
    temperature: float = 0.3,
) -> str:
    client = get_anthropic_client()
    last_error: Optional[Exception] = None

    for attempt in range(settings.anthropic_max_retries + 1):
        try:
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return extract_text_from_anthropic_response(response)
        except Exception as e:
            last_error = e
            print(f"[anthropic] attempt={attempt + 1} failed: {repr(e)}")
            if attempt < settings.anthropic_max_retries:
                time.sleep(2 ** attempt)

    raise last_error if last_error else RuntimeError("Unknown Anthropic error")


# ── Prompt builders ────────────────────────────────────────────────────────
def build_copy_prompt(user_request: str, ctx: Optional[BusinessContext]) -> str:
    company = ctx_company(ctx)
    audience = ctx_audience(ctx)
    offer = ctx_offer(ctx)
    tools = ctx_tools(ctx)
    goal = ctx_goal(ctx)

    return f"""You are a senior B2B marketing copywriter. You write concise, conversion-focused copy for email sequences, landing pages, outreach messages, and ads.

Business context:
- Company: {company}
- Offer: {offer}
- Audience: {audience}
- Tool stack: {tools}
- Goal: {goal}

You MUST return a valid JSON object matching this schema exactly. No markdown. No explanation. JSON only.

{{
  "summary": "string",
  "asset_type": "string",
  "target_audience": "string",
  "copy_brief": {{
    "company": "string",
    "offer": "string",
    "audience": "string",
    "goal": "string",
    "tone": "string",
    "cta": "string"
  }},
  "copy_framework": {{
    "problem": "string",
    "promise": "string",
    "proof": "string",
    "cta": "string"
  }},
  "copy": "string",
  "variants": ["string", "string", "string"],
  "sequence_outline": {{
    "sequence_type": "string",
    "email_1": "string",
    "email_2": "string",
    "email_3": "string",
    "email_4": "string",
    "email_5": "string"
  }},
  "notes": ["string"],
  "next_step": "string",
  "original_request": "string"
}}

Rules:
- Return valid JSON only
- Do not wrap in markdown fences
- Keep copy practical and usable as-is
- If underspecified, make a reasonable assumption and note it in "notes"
- original_request must be the exact user request below

User request:
\"\"\"{user_request}\"\"\"
"""


def build_campaign_strategy_prompt(user_request: str, ctx: Optional[BusinessContext]) -> str:
    company = ctx_company(ctx)
    audience = ctx_audience(ctx)
    offer = ctx_offer(ctx)
    industry = ctx_industry(ctx)
    tools = ctx_tools(ctx)
    goal = ctx_goal(ctx)

    return f"""You are a senior B2B demand generation strategist. You build focused, executable campaign strategies.

Business context:
- Company: {company}
- Industry: {industry}
- Offer: {offer}
- Audience: {audience}
- Tool stack: {tools}
- Goal: {goal}

You MUST return a valid JSON object matching this schema exactly. No markdown. No explanation. JSON only.

{{
  "summary": "string",
  "business_context_applied": {{
    "company": "string",
    "industry": "string",
    "offer": "string",
    "audience": "string",
    "goal": "string"
  }},
  "campaign_type": "string",
  "objective": "string",
  "icp": {{
    "primary_audience": "string",
    "industry_context": "string",
    "buying_trigger": "string",
    "pain_point": "string"
  }},
  "positioning": {{
    "problem": "string",
    "promise": "string",
    "differentiator": "string",
    "proof": "string"
  }},
  "channels": ["string"],
  "campaign_plan": ["string"],
  "risks": ["string"],
  "success_metrics": ["string"],
  "next_step": "string",
  "original_request": "string"
}}

Rules:
- Return valid JSON only
- Do not wrap in markdown fences
- Be specific and actionable, not generic
- If underspecified, make reasonable assumptions and note them in the risks or next_step fields
- original_request must be the exact user request below

User request:
\"\"\"{user_request}\"\"\"
"""


# ── Fallback builders ──────────────────────────────────────────────────────
def build_copy_fallback(
    user_request: str,
    ctx: Optional[BusinessContext],
    asset_type: str,
    sequence_length: str,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    company = ctx_company(ctx)
    audience = ctx_audience(ctx)
    offer = ctx_offer(ctx)
    tools = ctx_tools(ctx)
    goal = ctx_goal(ctx)

    notes = [
        f"This is a copy framework for {company}, not a final draft.",
        "Add specific proof points, metrics, and customer language before sending.",
        f"Final copy should be reviewed before loading into {tools}.",
    ]
    if error_message:
        notes.append(
            "Fallback mode was used because the live language model was unavailable."
        )

    return {
        "summary": f"{asset_type.title()} framework for {company} generated (fallback mode)." if error_message else f"{asset_type.title()} framework for {company} generated from your request.",
        "business_context_applied": {
            "company": company,
            "offer": offer,
            "audience": audience,
            "goal": goal,
        },
        "asset_type": asset_type,
        "target_audience": audience,
        "copy_brief": {
            "company": company,
            "offer": offer,
            "audience": audience,
            "goal": goal,
            "tone": "Direct, clear, benefit-led. No jargon.",
            "cta": "One primary CTA per piece. Make it specific to the next step.",
        },
        "copy_framework": {
            "problem": f"What pain does {audience} have that {offer} solves?",
            "promise": f"What outcome does {company} deliver and how fast?",
            "proof": "Specific result, customer outcome, or credibility signal.",
            "cta": "One action: book a call, reply, download, or start trial.",
        },
        "copy": "Draft a clear message with problem, promise, proof, and call to action.",
        "variants": [
            f"Short direct version — 3 sentences, pain point + outcome + CTA for {audience}",
            f"Value-led version — lead with the outcome {offer} delivers before the ask",
            f"Pain-point-led version — open with the exact problem {audience} faces before the solution",
        ],
        "sequence_outline": {
            "sequence_type": sequence_length,
            "email_1": f"Intro — who {company} is and the one problem you solve for {audience}",
            "email_2": f"Problem deepening — the specific cost of not solving it for {audience}",
            "email_3": f"Proof — specific result or case study relevant to {audience}",
            "email_4": f"Objection handling — the most common reason {audience} says no to {offer}",
            "email_5": f"CTA — clear ask tied to {goal}",
        },
        "notes": notes,
        "next_step": f"Provide the specific segment of {audience}, the exact offer details for {offer}, and the sending platform in {tools} to get production-ready copy.",
        "original_request": user_request,
    }


def build_campaign_fallback(
    user_request: str,
    ctx: Optional[BusinessContext],
    campaign_type: str,
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    company = ctx_company(ctx)
    audience = ctx_audience(ctx)
    offer = ctx_offer(ctx)
    industry = ctx_industry(ctx)
    tools = ctx_tools(ctx)
    goal = ctx_goal(ctx)

    risks = [
        f"Weak offer-market fit between {offer} and {audience} needs",
        "Too many channels at once before message is validated",
        "Landing page CTA misaligned to the ad or email promise",
        "No follow-up sequence after the first conversion event",
        f"Incorrect audience targeting in {tools} pulling the wrong segment",
    ]
    if error_message:
        risks.append(
            "Fallback mode was used because the live language model was unavailable."
        )

    return {
        "summary": f"{campaign_type.title()} strategy for {company} generated (fallback mode)." if error_message else f"{campaign_type.title()} strategy for {company} generated from your request.",
        "business_context_applied": {
            "company": company,
            "industry": industry,
            "offer": offer,
            "audience": audience,
            "goal": goal,
        },
        "campaign_type": campaign_type,
        "objective": f"Drive measurable progress toward {goal} for {company} by reaching {audience} with a focused message about {offer}.",
        "icp": {
            "primary_audience": audience,
            "industry_context": industry,
            "buying_trigger": f"The moment {audience} realizes they need {offer}",
            "pain_point": f"The core problem {offer} solves for {audience} in {industry}",
        },
        "positioning": {
            "problem": f"What does {audience} struggle with that {offer} solves?",
            "promise": f"What specific outcome does {company} deliver with {offer}?",
            "differentiator": f"Why {company} over alternatives for {audience} in {industry}?",
            "proof": "Specific result, stat, or customer outcome that validates the promise.",
        },
        "channels": [
            f"Email — nurture {audience} with proof-led sequences loaded into {tools}",
            f"Paid social — target {audience} in {industry} with one problem-led hook",
            "Landing page — single CTA aligned to the campaign offer",
            f"Outbound — direct outreach to qualified {audience} accounts",
        ],
        "campaign_plan": [
            f"Step 1 — Define the exact segment of {audience} and the one offer you are leading with.",
            f"Step 2 — Write one positioning statement: for {audience} who struggle with [X], {offer} delivers [Y] unlike [Z].",
            "Step 3 — Build landing page or conversion asset before launching any traffic.",
            f"Step 4 — Launch email and outbound first to {audience} — lower cost, faster feedback.",
            "Step 5 — Add paid only after the message is validated on warm traffic.",
            f"Step 6 — Review {primary_kpi_for_campaign(goal)} weekly and optimize the lowest-converting step.",
        ],
        "risks": risks,
        "success_metrics": [
            f"Primary KPI: {goal}",
            "Cost per qualified lead by channel",
            "Landing page conversion rate",
            "Email open and reply rate",
            "Meetings booked or pipeline created",
        ],
        "next_step": f"Confirm the exact segment of {audience}, the single offer, and the primary channel so a build-ready campaign brief can be created for {company}.",
        "original_request": user_request,
    }


# ── Workers ────────────────────────────────────────────────────────────────
@traceable(name="worker_crm_ops")
def run_crm_ops(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    request_lower = user_request.lower()

    company = ctx_company(ctx)
    tools = ctx_tools(ctx)
    audience = ctx_audience(ctx)
    goal = ctx_goal(ctx)

    workflow_type = "general CRM workflow"
    if "mql" in request_lower and "sql" in request_lower:
        workflow_type = "MQL to SQL handoff workflow"
    elif "lead routing" in request_lower or "assign" in request_lower:
        workflow_type = "lead routing workflow"
    elif "lifecycle" in request_lower:
        workflow_type = "lifecycle stage workflow"
    elif "re-engagement" in request_lower or "reengagement" in request_lower:
        workflow_type = "re-engagement workflow"
    elif "sla" in request_lower:
        workflow_type = "SLA enforcement workflow"

    trigger = "Form submission or lifecycle stage update"
    if "form" in request_lower:
        trigger = "Specific form submission"
    elif "score" in request_lower:
        trigger = "Lead score threshold reached"
    elif "booked call" in request_lower or "meeting" in request_lower:
        trigger = "Meeting booked event"
    elif "mql" in request_lower:
        trigger = "Lifecycle stage becomes MQL"

    assignment_model = "round robin"
    if "territory" in request_lower:
        assignment_model = "territory-based routing"
    elif "segment" in request_lower:
        assignment_model = "segment-based routing"
    elif "weighted" in request_lower:
        assignment_model = "weighted round robin"

    return {
        "summary": f"{workflow_type} for {company} generated from your request.",
        "business_context_applied": {
            "company": company,
            "tool_stack": tools,
            "audience": audience,
            "workflow_goal": goal,
        },
        "request_interpreted_as": workflow_type,
        "workflow_readiness": "approval_required_before_live_execution",
        "goal": f"Create a build-ready {workflow_type} spec for {company} that can be reviewed by ops before implementation in {tools}.",
        "recommended_actions": [
            f"Align {company} sales team on exact qualification and routing criteria before activation.",
            "Use one clear enrollment trigger and avoid overlapping workflow logic.",
            "Define a fallback owner or queue for records that do not meet routing conditions.",
            "Stamp workflow metadata for reporting, SLA checks, and auditability.",
            "Test using sample records before any live rollout.",
        ],
        "workflow_blueprint": {
            "workflow_name": f"{company} — {workflow_type}",
            "objective": f"Move qualified {audience} leads through a controlled handoff with clear ownership, lifecycle updates, notifications, and escalation rules.",
            "trigger": trigger,
            "assignment_model": assignment_model,
            "entry_conditions": [
                "Record meets the primary qualification threshold",
                "Record is not disqualified",
                "Record is not already owned by the intended rep",
                "Required routing fields are present or can be defaulted",
            ],
            "suppression_rules": [
                "Do not enroll records already in SQL or Opportunity stage",
                "Do not enroll records routed in the last 24 hours",
                "Do not enroll records already assigned correctly",
                "Do not enroll records marked unqualified or disqualified",
            ],
            "branches": [
                {
                    "step": 1,
                    "name": "Qualification check",
                    "logic": "Verify that the record meets the qualification threshold and is eligible for routing.",
                    "if_true": "Continue to data readiness check",
                    "if_false": "Exit or route to manual review",
                },
                {
                    "step": 2,
                    "name": "Data readiness check",
                    "logic": "Validate required routing fields such as territory, segment, lifecycle stage, lead source, and score.",
                    "if_true": "Continue to assignment logic",
                    "if_false": "Send to fallback queue and notify ops",
                },
                {
                    "step": 3,
                    "name": "Owner assignment",
                    "logic": f"Assign owner based on {assignment_model}.",
                    "if_true": "Stamp assignment metadata and continue",
                    "if_false": "Assign fallback owner and raise internal alert",
                },
                {
                    "step": 4,
                    "name": "Lifecycle and status update",
                    "logic": "Update lifecycle stage, lead status, and handoff metadata fields.",
                    "if_true": "Continue to notifications",
                    "if_false": "Log issue and notify ops for review",
                },
                {
                    "step": 5,
                    "name": "Internal notification",
                    "logic": f"Notify the assigned owner and relevant {company} team channel with context for next action.",
                    "if_true": "Continue to SLA monitoring",
                    "if_false": "Escalate to manager or queue owner",
                },
                {
                    "step": 6,
                    "name": "SLA check",
                    "logic": "After a defined delay, verify follow-up activity or stage movement occurred.",
                    "if_true": "Mark workflow complete",
                    "if_false": "Escalate for missed SLA",
                },
            ],
            "fallback_path": {
                "condition": "No valid routing match or required fields are missing",
                "action": f"Assign to {company} queue manager or default owner and create an internal alert for manual review",
            },
            "exit_criteria": [
                "Record has been assigned and stamped successfully",
                "Record is disqualified",
                "Record was recently routed",
                "Record was sent to manual review due to missing data",
            ],
        },
        "hubspot_fields_to_confirm": [
            "Lifecycle stage",
            "Lead status",
            "HubSpot owner",
            "Lead score",
            "Original source",
            "Latest conversion",
            "Territory",
            "Segment",
            "Handoff date",
            "Routing method",
            "SLA breach flag",
        ],
        "suggested_property_stamps": [
            "mql_date",
            "sql_handoff_date",
            "routing_method",
            "assigned_team",
            "handoff_source",
            "sla_deadline",
            "sla_breach_flag",
            "workflow_version",
        ],
        "notification_plan": {
            "internal_alerts": [
                "Notify assigned owner on assignment",
                "Notify ops if fallback path is used",
                "Notify manager if SLA is breached",
            ],
            "recommended_channels": [
                f"{tools} internal notification" if tools != "your CRM and tool stack" else "HubSpot internal email notification",
                "Slack alert to sales or ops channel",
            ],
        },
        "risk_notes": [
            "Overlapping workflows can cause duplicate routing or conflicting updates",
            "Missing routing fields can break owner assignment logic",
            "Lifecycle stage changes may conflict with other active automations",
            "Fallback ownership must always exist to avoid orphaned records",
            "SLA checks should be tested carefully before going live",
        ],
        "qa_checklist": [
            "Verify re-enrollment settings",
            "Check that fallback path always assigns an owner",
            "Confirm suppression rules prevent duplicate routing",
            "Test notifications with sample records",
            "Validate lifecycle stage updates against existing automations",
            "Validate SLA timing and escalation behavior",
        ],
        "approval_required": True,
        "safe_execution_policy": "This route may recommend operational changes but should not execute live CRM changes automatically.",
        "next_step": f"Provide the exact object type, trigger, qualification rule, assignment logic, and fallback owner for {company} if you want a near-build-ready {tools} implementation spec.",
        "original_request": user_request,
    }


@traceable(name="worker_reporting")
def run_reporting(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    request_lower = user_request.lower()

    company = ctx_company(ctx)
    tools = ctx_tools(ctx)
    audience = ctx_audience(ctx)

    analysis_type = "general performance analysis"
    if "drop" in request_lower or "decline" in request_lower or "fell" in request_lower or "down" in request_lower:
        analysis_type = "performance decline diagnostic"
    elif "conversion" in request_lower:
        analysis_type = "conversion rate analysis"
    elif "attribution" in request_lower:
        analysis_type = "attribution analysis"
    elif "funnel" in request_lower:
        analysis_type = "funnel stage analysis"
    elif "kpi" in request_lower or "dashboard" in request_lower:
        analysis_type = "KPI dashboard review"
    elif "roi" in request_lower or "return" in request_lower:
        analysis_type = "ROI and spend analysis"

    primary_kpi = "conversion rate"
    if "booked call" in request_lower or "meeting" in request_lower:
        primary_kpi = "meetings booked"
    elif "revenue" in request_lower:
        primary_kpi = "revenue attributed"
    elif "lead" in request_lower and "quality" in request_lower:
        primary_kpi = "lead quality score"
    elif "open rate" in request_lower or "email" in request_lower:
        primary_kpi = "email open and click rate"
    elif "cpl" in request_lower or "cost per lead" in request_lower:
        primary_kpi = "cost per lead"
    elif "cac" in request_lower or "cost per acquisition" in request_lower:
        primary_kpi = "customer acquisition cost"
    elif "paid" in request_lower or "ads" in request_lower:
        primary_kpi = "paid channel conversion rate"
    elif "organic" in request_lower or "seo" in request_lower:
        primary_kpi = "organic traffic and conversion"

    return {
        "summary": f"{analysis_type.title()} for {company} generated from your request.",
        "business_context_applied": {
            "company": company,
            "tool_stack": tools,
            "audience": audience,
        },
        "request_interpreted_as": analysis_type,
        "primary_kpi": primary_kpi,
        "diagnostic_framework": {
            "step_1_define": {
                "label": "Define the measurement scope",
                "questions": [
                    f"What is the exact {primary_kpi} baseline for {company}?",
                    "What is the time period and comparison baseline?",
                    "What traffic source or segment is the focus?",
                    "What funnel stage or lifecycle stage is relevant?",
                ],
            },
            "step_2_segment": {
                "label": "Segment and compare",
                "actions": [
                    f"Break {primary_kpi} down by source, channel, and campaign for {company}.",
                    "Compare current period against prior period and prior year same period.",
                    "Identify the segment with the steepest change.",
                    "Check if the trend is isolated to one source or systemic across all channels.",
                ],
            },
            "step_3_diagnose": {
                "label": "Diagnose the likely causes",
                "likely_causes": [
                    f"Lead quality change from a specific source targeting {audience}",
                    "Offer or message mismatch reducing downstream conversion",
                    "Routing or automation change affecting handoff speed or accuracy",
                    "Seasonal or market-driven demand change",
                    "Attribution change or tracking error inflating or deflating numbers",
                    "A/B test or copy change that shifted performance",
                ],
            },
            "step_4_investigate": {
                "label": "Investigate the data",
                "where_to_look": [
                    f"{tools} reports: source breakdown, lifecycle stage conversion rates, workflow enrollment data",
                    "Paid channel dashboards: CPL, CTR, quality score trends",
                    "Email platform: open rate, click rate, reply rate trends",
                    "CRM activity: sales follow-up time, lead status movement, meeting booking rate",
                    "Attribution model: check for changes in UTM coverage or channel credit logic",
                ],
            },
            "step_5_recommend": {
                "label": "Recommended actions",
                "actions": [
                    "Isolate the one metric with the largest negative change.",
                    "Compare before/after for any operational or campaign changes in that period.",
                    "Check whether the issue is traffic volume, traffic quality, or conversion mechanics.",
                    "Run a source-level comparison to confirm if the issue is one channel or cross-channel.",
                    f"Audit the last 3 changes made to {company} routing, automation, copy, or targeting in the affected period.",
                ],
            },
        },
        "key_metrics_to_pull": [
            f"{primary_kpi} by source",
            f"{primary_kpi} by campaign",
            "Lead to MQL conversion rate",
            "MQL to SQL conversion rate",
            "SQL to opportunity conversion rate",
            "Average days per funnel stage",
            "Meeting booked rate by source",
            "Lead status movement by rep",
            "Workflow enrollment and completion rate",
            "Cost per lead by channel",
        ],
        "questions_to_answer_first": [
            "What is the exact KPI that changed?",
            "When exactly did the change start?",
            "Is it one channel or all channels?",
            "What changed operationally in that same period?",
            "Is it a volume problem or a conversion rate problem?",
        ],
        "common_reporting_mistakes": [
            "Measuring revenue without controlling for lag between lead creation and close",
            "Comparing periods with different campaign budgets or targeting without noting that",
            "Attributing all changes to one cause without segmenting the data",
            "Ignoring attribution model changes that can inflate or deflate source credit",
            f"Pulling reports without filtering for the correct lifecycle stage or contact type in {tools}",
        ],
        "next_step": f"Provide the specific KPI, time period, and suspected source for {company} to get a tighter diagnostic.",
        "original_request": user_request,
    }


@traceable(name="worker_copy")
def run_copy(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    request_lower = user_request.lower()

    asset_type = "marketing copy"
    if "email" in request_lower or "nurture" in request_lower:
        asset_type = "email sequence"
    elif "landing page" in request_lower:
        asset_type = "landing page copy"
    elif "outreach" in request_lower:
        asset_type = "outreach message"
    elif "ad" in request_lower:
        asset_type = "ad copy"

    sequence_length = "5-email"
    if "3" in request_lower or "three" in request_lower:
        sequence_length = "3-email"
    elif "7" in request_lower or "seven" in request_lower:
        sequence_length = "7-email"

    try:
        raw_json = call_anthropic_json(
            system_prompt="You generate concise, useful B2B marketing copy and always return strict JSON with no markdown.",
            user_prompt=build_copy_prompt(user_request, ctx),
            max_tokens=1400,
            temperature=0.4,
        )
        validated = CopyWorkerOutput.model_validate_json(raw_json)
        result = validated.model_dump()
        result["business_context_applied"] = {
            "company": ctx_company(ctx),
            "offer": ctx_offer(ctx),
            "audience": ctx_audience(ctx),
            "goal": ctx_goal(ctx),
        }
        return result
    except ValidationError as e:
        print("[copy] validation error:", repr(e))
        return build_copy_fallback(
            user_request=user_request,
            ctx=ctx,
            asset_type=asset_type,
            sequence_length=sequence_length,
            error_message=f"Validation error: {str(e)}",
        )
    except Exception as e:
        print("[copy] runtime error:", repr(e))
        return build_copy_fallback(
            user_request=user_request,
            ctx=ctx,
            asset_type=asset_type,
            sequence_length=sequence_length,
            error_message=str(e),
        )


def primary_kpi_for_campaign(goal: str) -> str:
    goal_lower = goal.lower()
    if "lead" in goal_lower:
        return "leads generated"
    if "book" in goal_lower or "call" in goal_lower or "meeting" in goal_lower:
        return "meetings booked"
    if "revenue" in goal_lower or "pipeline" in goal_lower:
        return "pipeline created"
    if "conversion" in goal_lower:
        return "conversion rate"
    return "primary campaign KPI"


@traceable(name="worker_campaign_strategy")
def run_campaign_strategy(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    request_lower = user_request.lower()

    campaign_type = "full-funnel campaign"
    if "launch" in request_lower:
        campaign_type = "product or offer launch campaign"
    elif "nurture" in request_lower:
        campaign_type = "nurture campaign"
    elif "retarget" in request_lower or "re-engage" in request_lower:
        campaign_type = "re-engagement campaign"
    elif "awareness" in request_lower:
        campaign_type = "brand awareness campaign"
    elif "outbound" in request_lower:
        campaign_type = "outbound campaign"

    try:
        raw_json = call_anthropic_json(
            system_prompt="You generate specific, actionable B2B campaign strategies and always return strict JSON with no markdown.",
            user_prompt=build_campaign_strategy_prompt(user_request, ctx),
            max_tokens=1400,
            temperature=0.3,
        )
        validated = CampaignWorkerOutput.model_validate_json(raw_json)
        return validated.model_dump()
    except ValidationError as e:
        print("[campaign_strategy] validation error:", repr(e))
        return build_campaign_fallback(
            user_request=user_request,
            ctx=ctx,
            campaign_type=campaign_type,
            error_message=f"Validation error: {str(e)}",
        )
    except Exception as e:
        print("[campaign_strategy] runtime error:", repr(e))
        return build_campaign_fallback(
            user_request=user_request,
            ctx=ctx,
            campaign_type=campaign_type,
            error_message=str(e),
        )


@traceable(name="worker_research")
def run_research(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    company = ctx_company(ctx)
    audience = ctx_audience(ctx)
    offer = ctx_offer(ctx)
    industry = ctx_industry(ctx)
    goal = ctx_goal(ctx)

    request_lower = user_request.lower()

    research_type = "market and competitor research"
    if "competitor" in request_lower or "competition" in request_lower:
        research_type = "competitor analysis"
    elif "persona" in request_lower:
        research_type = "buyer persona research"
    elif "market" in request_lower:
        research_type = "market landscape research"
    elif "positioning" in request_lower:
        research_type = "positioning and messaging research"

    return {
        "summary": f"{research_type.title()} brief for {company} in {industry} generated from your request.",
        "business_context_applied": {
            "company": company,
            "industry": industry,
            "offer": offer,
            "audience": audience,
            "goal": goal,
        },
        "research_type": research_type,
        "research_scope": {
            "company_context": f"{company} operates in {industry} selling {offer} to {audience}",
            "primary_goal": f"Inform {goal} with market and competitive intelligence",
            "key_question": f"What do {audience} in {industry} need that {company} can uniquely deliver?",
        },
        "findings_framework": [
            f"Identify the top 3 to 5 direct competitors to {company} in {industry}",
            "Review how each competitor frames the problem, promise, and proof",
            "Extract repeated buyer language, pain points, and objections across reviews and content",
            f"Find positioning gaps where {offer} is differentiated but underarticulated",
            "Capture credibility markers competitors use: case studies, stats, client logos",
        ],
        "implications": [
            f"Use a differentiation angle specific to {audience} that competitors are not owning",
            f"Match the exact language {audience} use to describe their problem — not {company}'s internal language",
            "Support claims with concrete proof points before scaling paid or outbound",
            f"Position {offer} against the category problem, not just against individual competitors",
        ],
        "open_questions": [
            f"Which specific segment of {audience} is the highest priority for {company} right now?",
            f"Which 3 to 5 competitors are most directly stealing {company}'s deals?",
            f"What is the #1 objection {audience} gives when they do not buy {offer}?",
            f"What proof do {audience} in {industry} trust most: stats, case studies, or peer referrals?",
        ],
        "recommended_next_steps": [
            f"List the top 3 direct competitors to {company} in {industry}",
            "Pull their homepage, pricing page, and one case study for messaging analysis",
            f"Search G2, Capterra, or Reddit for reviews from {audience} about alternatives to {offer}",
            "Build a positioning matrix: problem framing, promise, proof, and CTA for each competitor",
            f"Use findings to sharpen {company}'s ICP definition and messaging for {goal}",
        ],
        "next_step": f"Confirm the 3 competitors and the specific segment of {audience} you want analyzed to get a tighter research brief for {company}.",
        "original_request": user_request,
    }


@traceable(name="worker_clarify")
def run_clarify(user_request: str, missing_inputs: List[str], ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    company = ctx_company(ctx)
    return {
        "summary": f"Need clarification before proceeding{' for ' + company if company != 'your company' else ''}.",
        "questions": missing_inputs,
        "why_it_matters": [
            "The supervisor needs a clear task type before assigning the right specialist."
        ],
        "original_request": user_request,
    }


@traceable(name="worker_reject")
def run_reject(user_request: str, ctx: Optional[BusinessContext] = None) -> Dict[str, Any]:
    return {
        "summary": "Request cannot be completed as a live operational action.",
        "reason": "This supervisor can recommend actions, but should not execute risky live changes automatically.",
        "safe_alternative": "Ask for a change plan, draft workflow spec, or approval-ready execution checklist instead.",
        "original_request": user_request,
    }


# ── Reviewer ───────────────────────────────────────────────────────────────
def review_result(route: str, worker_output: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "needs_revision": False,
        "issues": [],
        "final_response": {
            "route_used": route,
            "deliverable": worker_output,
            "next_step": "Review the output and refine the request if you want a more specific deliverable.",
            "max_steps": MAX_STEPS,
        },
    }


# ── Endpoints ──────────────────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "Marketing Ops Agent Supervisor backend is running.",
        "model": settings.anthropic_model,
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "anthropic_configured": bool(settings.anthropic_api_key),
        "model": settings.anthropic_model,
    }


@app.post("/run")
@traceable(name="supervisor_run")
def run_supervisor(req: RunRequest):
    ctx = req.business_context

    decision = route_request(req.input)

    if decision.route not in ALLOWED_ROUTES:
        decision = RouteDecision(
            route="clarify",
            confidence=0.50,
            reason="Route was invalid and was reset to clarify.",
            missing_inputs=[
                "Describe the exact outcome you want: CRM ops, reporting, copy, campaign strategy, or research."
            ],
            risk_level="low",
            requires_human_approval=False,
        )

    print("ROUTE:", decision.route)
    print("RISK LEVEL:", decision.risk_level)
    print("APPROVAL REQUIRED:", decision.requires_human_approval)
    print("MODEL:", settings.anthropic_model)
    print("CONTEXT:", ctx.model_dump() if ctx else "none provided")

    if decision.route == "crm_ops":
        worker_output = run_crm_ops(req.input, ctx)
    elif decision.route == "reporting":
        worker_output = run_reporting(req.input, ctx)
    elif decision.route == "copy":
        worker_output = run_copy(req.input, ctx)
    elif decision.route == "campaign_strategy":
        worker_output = run_campaign_strategy(req.input, ctx)
    elif decision.route == "research":
        worker_output = run_research(req.input, ctx)
    elif decision.route == "reject":
        worker_output = run_reject(req.input, ctx)
    else:
        worker_output = run_clarify(req.input, decision.missing_inputs, ctx)

    review = review_result(decision.route, worker_output)

    return {
        "decision": decision.model_dump(),
        "result": review["final_response"],
    }