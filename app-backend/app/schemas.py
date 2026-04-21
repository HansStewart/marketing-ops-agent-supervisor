from pydantic import BaseModel, Field
from typing import List, Literal

class IntakeRoute(BaseModel):
    request_type: Literal["lead_intake", "campaign_brief", "record_audit"]
    reasoning: str

class PlanStep(BaseModel):
    step_name: str
    owner: Literal["hubspot_worker", "content_worker", "reporting_worker"]
    objective: str

class PlanOutput(BaseModel):
    steps: List[PlanStep]

class EvalOutput(BaseModel):
    pass_fail: Literal["pass", "fail"]
    score: int = Field(ge=0, le=100)
    feedback: str
    approval_required: bool