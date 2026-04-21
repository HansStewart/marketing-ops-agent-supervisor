export type BusinessContext = {
  company_name: string;
  industry: string;
  primary_offer: string;
  target_audience: string;
  tool_stack: string;
  workflow_goal: string;
};

export type RunResponse = {
  decision: {
    route: string;
    confidence: number;
    reason: string;
    missing_inputs: string[];
    risk_level: string;
    requires_human_approval: boolean;
  };
  result: {
    route_used: string;
    deliverable: Record<string, unknown>;
    next_step: string;
  };
};

export type HealthResponse = {
  status: string;
  anthropic_configured?: boolean;
  model?: string;
};

const API_BASE = "http://127.0.0.1:8000";

export async function runAgent(
  input: string,
  businessContext: BusinessContext
): Promise<RunResponse> {
  const response = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input, business_context: businessContext }),
  });
  if (!response.ok) throw new Error(`Failed to run agent: ${response.status}`);
  return response.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error(`Failed health: ${response.status}`);
  return response.json();
}