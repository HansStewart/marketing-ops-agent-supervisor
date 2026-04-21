import React, { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import { BusinessContext, runAgent, RunResponse } from "./api";
import "./App.css";

type NavView = "requests" | "runs" | "hubspot" | "evaluations" | "settings";

const defaultBusinessContext: BusinessContext = {
  company_name: "",
  industry: "",
  primary_offer: "",
  target_audience: "",
  tool_stack: "",
  workflow_goal: "",
};

const demoScenarios = [
  {
    label: "Booked Call Drop",
    prompt:
      "Reporting - analyze why booked calls dropped from paid search leads last month.",
  },
  {
    label: "MQL to SQL Handoff",
    prompt:
      "Build a HubSpot workflow for MQL to SQL handoff using round robin assignment with a fallback owner and 2-hour SLA check.",
  },
  {
    label: "Nurture Copy",
    prompt:
      "Write a 5-email nurture sequence for inbound leads from paid search who did not book a call.",
  },
  {
    label: "Campaign Strategy",
    prompt:
      "Create a go-to-market campaign plan for a new SMB offer targeting roofing contractors.",
  },
  {
    label: "Competitor Research",
    prompt:
      "Research how the top 3 HubSpot competitors position their CRM automation for SMBs.",
  },
];

const ROUTE_NODES = [
  { key: "intake", label: "Intake Router" },
  { key: "crm_ops", label: "CRM Ops Worker" },
  { key: "reporting", label: "Reporting Worker" },
  { key: "copy", label: "Copy Worker" },
  { key: "campaign_strategy", label: "Campaign Strategy Worker" },
  { key: "research", label: "Research Worker" },
  { key: "reviewer", label: "Final Reviewer" },
];

const RISK_COLORS: Record<string, string> = {
  low: "status-completed",
  medium: "status-pending_approval",
  high: "status-pending_approval",
};

function formatLabel(input: string): string {
  return input.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function isPrimitive(v: unknown): v is string | number | boolean | null {
  return (
    typeof v === "string" ||
    typeof v === "number" ||
    typeof v === "boolean" ||
    v === null
  );
}

function objectToMarkdown(value: unknown, depth = 0): string {
  const pad = "  ".repeat(depth);

  if (isPrimitive(value)) {
    return `${value ?? "—"}`;
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (isPrimitive(item)) {
          return `${pad}- ${item ?? "—"}`;
        }

        if (typeof item === "object" && item !== null && !Array.isArray(item)) {
          const entries = Object.entries(item as Record<string, unknown>);
          const allPrimitive = entries.every(([, v]) => isPrimitive(v));

          if (allPrimitive) {
            const inner = entries
              .map(([k, v]) => `${pad}  - **${formatLabel(k)}:** ${v ?? "—"}`)
              .join("\n");
            return `${pad}-\n${inner}`;
          }

          const inner = entries
            .map(([k, v]) => {
              if (isPrimitive(v)) {
                return `${pad}  - **${formatLabel(k)}:** ${v ?? "—"}`;
              }
              return `${pad}  - **${formatLabel(k)}:**\n${objectToMarkdown(
                v,
                depth + 2
              )}`;
            })
            .join("\n");
          return `${pad}-\n${inner}`;
        }

        if (Array.isArray(item)) {
          return `${pad}-\n${objectToMarkdown(item, depth + 1)}`;
        }

        return `${pad}- ${String(item)}`;
      })
      .join("\n");
  }

  if (typeof value === "object" && value !== null) {
    return Object.entries(value as Record<string, unknown>)
      .map(([k, v]) => {
        if (isPrimitive(v)) {
          return `${pad}- **${formatLabel(k)}:** ${v ?? "—"}`;
        }
        if (Array.isArray(v)) {
          return `${pad}- **${formatLabel(k)}:**\n${objectToMarkdown(
            v,
            depth + 1
          )}`;
        }
        return `${pad}- **${formatLabel(k)}:**\n${objectToMarkdown(
          v,
          depth + 1
        )}`;
      })
      .join("\n");
  }

  return String(value);
}

function formatDeliverable(deliverable: Record<string, unknown>): string {
  return Object.entries(deliverable)
    .filter(([key]) => key !== "original_request" && key !== "summary")
    .map(([key, value]) => {
      const heading = `## ${formatLabel(key)}`;

      if (isPrimitive(value)) {
        return `${heading}\n\n${value ?? "—"}`;
      }

      return `${heading}\n\n${objectToMarkdown(value)}`;
    })
    .join("\n\n---\n\n");
}

function extractErrorItems(items: unknown): string[] {
  if (!Array.isArray(items)) return [];
  return items.filter(
    (item): item is string =>
      typeof item === "string" &&
      (item.startsWith("LLM error") || item.startsWith("Validation error"))
  );
}

function renderCopyOutput(deliverable: Record<string, unknown>): React.ReactElement {
  const errorNotes = extractErrorItems(deliverable.notes);
  const summary =
    typeof deliverable.summary === "string" ? deliverable.summary : "";

  return React.createElement(
    "div",
    { className: "markdown-output" },
    [
      errorNotes.length > 0
        ? React.createElement(
            React.Fragment,
            { key: "system-note" },
            React.createElement("h3", null, "System Note"),
            React.createElement(
              "ul",
              null,
              errorNotes.map((note, i) =>
                React.createElement("li", { key: i }, note)
              )
            )
          )
        : null,

      summary
        ? React.createElement(
            React.Fragment,
            { key: "summary" },
            React.createElement("h3", null, "Summary"),
            React.createElement("p", null, summary)
          )
        : null,

      deliverable.copy
        ? React.createElement(
            React.Fragment,
            { key: "copy-draft" },
            React.createElement("h3", null, "Copy Draft"),
            React.createElement(ReactMarkdown, null, String(deliverable.copy))
          )
        : null,

      deliverable.copy_brief
        ? React.createElement(
            React.Fragment,
            { key: "copy-brief" },
            React.createElement("h3", null, "Copy Brief"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.copy_brief)
            )
          )
        : null,

      deliverable.copy_framework
        ? React.createElement(
            React.Fragment,
            { key: "copy-framework" },
            React.createElement("h3", null, "Copy Framework"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.copy_framework)
            )
          )
        : null,

      deliverable.variants
        ? React.createElement(
            React.Fragment,
            { key: "variants" },
            React.createElement("h3", null, "Variants"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.variants)
            )
          )
        : null,

      deliverable.sequence_outline
        ? React.createElement(
            React.Fragment,
            { key: "sequence-outline" },
            React.createElement("h3", null, "Sequence Outline"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.sequence_outline)
            )
          )
        : null,

      deliverable.notes
        ? React.createElement(
            React.Fragment,
            { key: "notes" },
            React.createElement("h3", null, "Notes"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.notes)
            )
          )
        : null,
    ].filter(Boolean)
  );
}

function renderCampaignOutput(
  deliverable: Record<string, unknown>
): React.ReactElement {
  const errorRisks = extractErrorItems(deliverable.risks);
  const summary =
    typeof deliverable.summary === "string" ? deliverable.summary : "";

  return React.createElement(
    "div",
    { className: "markdown-output" },
    [
      errorRisks.length > 0
        ? React.createElement(
            React.Fragment,
            { key: "system-note" },
            React.createElement("h3", null, "System Note"),
            React.createElement(
              "ul",
              null,
              errorRisks.map((note, i) =>
                React.createElement("li", { key: i }, note)
              )
            )
          )
        : null,

      summary
        ? React.createElement(
            React.Fragment,
            { key: "summary" },
            React.createElement("h3", null, "Summary"),
            React.createElement("p", null, summary)
          )
        : null,

      deliverable.objective
        ? React.createElement(
            React.Fragment,
            { key: "objective" },
            React.createElement("h3", null, "Objective"),
            React.createElement("p", null, String(deliverable.objective))
          )
        : null,

      deliverable.business_context_applied
        ? React.createElement(
            React.Fragment,
            { key: "business-context" },
            React.createElement("h3", null, "Business Context Applied"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.business_context_applied)
            )
          )
        : null,

      deliverable.icp
        ? React.createElement(
            React.Fragment,
            { key: "icp" },
            React.createElement("h3", null, "ICP"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.icp)
            )
          )
        : null,

      deliverable.positioning
        ? React.createElement(
            React.Fragment,
            { key: "positioning" },
            React.createElement("h3", null, "Positioning"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.positioning)
            )
          )
        : null,

      deliverable.channels
        ? React.createElement(
            React.Fragment,
            { key: "channels" },
            React.createElement("h3", null, "Channels"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.channels)
            )
          )
        : null,

      deliverable.campaign_plan
        ? React.createElement(
            React.Fragment,
            { key: "campaign-plan" },
            React.createElement("h3", null, "Campaign Plan"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.campaign_plan)
            )
          )
        : null,

      deliverable.success_metrics
        ? React.createElement(
            React.Fragment,
            { key: "success-metrics" },
            React.createElement("h3", null, "Success Metrics"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.success_metrics)
            )
          )
        : null,

      deliverable.risks
        ? React.createElement(
            React.Fragment,
            { key: "risks" },
            React.createElement("h3", null, "Risks"),
            React.createElement(
              ReactMarkdown,
              null,
              objectToMarkdown(deliverable.risks)
            )
          )
        : null,
    ].filter(Boolean)
  );
}

function App() {
  const [navView, setNavView] = useState<NavView>("requests");
  const [input, setInput] = useState(
    "Reporting - analyze why booked calls dropped from paid search leads last month."
  );
  const [businessContext, setBusinessContext] =
    useState<BusinessContext>(defaultBusinessContext);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [approved, setApproved] = useState(false);
  const [showRawRun, setShowRawRun] = useState(false);

  const updateBusinessField = (
    field: keyof BusinessContext,
    value: string
  ) => {
    setBusinessContext((prev) => ({ ...prev, [field]: value }));
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setApproved(false);
    try {
      const data = await runAgent(input, businessContext);
      setResult(data);
      setNavView("requests");
    } catch (err) {
      console.error(err);
      setError("Something went wrong while running the supervisor.");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = () => {
    setApproved(true);
  };

  const graphNodes = useMemo(() => {
    const activeRoute = result?.decision?.route;
    return ROUTE_NODES.map((node) => ({
      ...node,
      done:
        node.key === "intake"
          ? !!result
          : node.key === activeRoute
          ? true
          : node.key === "reviewer"
          ? !!result
          : false,
    }));
  }, [result]);

  const route = result?.decision?.route ?? "";
  const confidence = result?.decision?.confidence ?? 0;
  const riskLevel = result?.decision?.risk_level ?? "low";
  const requiresApproval = result?.decision?.requires_human_approval ?? false;
  const deliverable = result?.result?.deliverable ?? null;
  const nextStep = result?.result?.next_step ?? "";

  const summaryText =
    deliverable && typeof deliverable.summary === "string"
      ? deliverable.summary
      : null;

  const formattedDeliverable = deliverable
    ? formatDeliverable(deliverable as Record<string, unknown>)
    : "";

  const statusLabel = approved
    ? "approved"
    : requiresApproval
    ? "pending_approval"
    : result
    ? "completed"
    : "pending";

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true"></div>
          <div>
            <div className="brand-eyebrow">AI Operator Console</div>
            <div className="brand-title">Business Workflow Supervisor</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {(
            [
              ["requests", "Requests"],
              ["runs", "Decision Trace"],
              ["hubspot", "CRM Records"],
              ["evaluations", "Route Review"],
              ["settings", "Settings"],
            ] as [NavView, string][]
          ).map(([view, label]) => (
            <button
              key={view}
              className={`nav-item ${navView === view ? "active" : ""}`}
              onClick={() => setNavView(view)}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <div className="sidebar-label">System Status</div>
          <div className="status-row">
            <span className="status-dot live"></span>
            <span>Backend Connected</span>
          </div>
          <div className="status-row">
            <span className="status-dot ready"></span>
            <span>Deterministic Router</span>
          </div>
          <div className="status-row">
            <span className="status-dot demo"></span>
            <span>Structured Worker Mode</span>
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div>
            <h1>Business Workflow Supervisor</h1>
            <p>
              Operator console for supervised marketing ops workflow execution.
            </p>
          </div>
          <div className="topbar-meta">
            <span className="meta-pill">Deterministic Routing</span>
            <span className="meta-pill">Human Approval Gate</span>
            <span className="meta-pill">Structured Outputs</span>
          </div>
        </header>

        <main className="main-grid">
          <section className="column column-left">
            <div className="card hero-card">
              <div className="section-label">Business Context</div>
              <h2>Configure the business</h2>
              <p className="muted">
                Define the company, offer, audience, and systems so the
                supervisor can tailor the workflow.
              </p>
              <div className="form-grid">
                {(
                  [
                    ["company_name", "Company name"],
                    ["industry", "Industry"],
                    ["primary_offer", "Primary offer"],
                    ["target_audience", "Target audience"],
                    ["tool_stack", "CRM / tool stack"],
                    ["workflow_goal", "Workflow goal"],
                  ] as [keyof BusinessContext, string][]
                ).map(([field, placeholder]) => (
                  <input
                    key={field}
                    type="text"
                    placeholder={placeholder}
                    value={businessContext[field]}
                    onChange={(e) => updateBusinessField(field, e.target.value)}
                  />
                ))}
              </div>
            </div>

            <div className="card">
              <div className="section-label">Request Intake</div>
              <h2>Run a supervised agent workflow</h2>
              <p className="muted">
                Submit a business request. The supervisor will classify, route
                to the correct worker, and return a structured deliverable.
              </p>
              <div className="scenario-row">
                {demoScenarios.map((scenario) => (
                  <button
                    key={scenario.label}
                    className="scenario-chip"
                    onClick={() => setInput(scenario.prompt)}
                    type="button"
                  >
                    {scenario.label}
                  </button>
                ))}
              </div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                rows={6}
              />
              <div className="action-row">
                <button onClick={handleRun} disabled={loading}>
                  {loading ? "Running supervisor..." : "Run Agent"}
                </button>
                <span className="helper-text">
                  Routes to: crm_ops · reporting · copy · campaign_strategy ·
                  research · clarify · reject
                </span>
              </div>
              {error && <p className="error">{error}</p>}
            </div>

            <div className="card">
              <div className="section-label">Workflow Graph</div>
              <h2>Execution status</h2>
              <div className="graph-list">
                {graphNodes.map((node, idx) => (
                  <div
                    key={node.key}
                    className={`graph-node ${node.done ? "done" : ""}`}
                  >
                    <div className="graph-index">{idx + 1}</div>
                    <div className="graph-content">
                      <div className="graph-title">{node.label}</div>
                      <div className="graph-state">
                        {node.done
                          ? node.key === "intake" || node.key === "reviewer"
                            ? "Completed"
                            : "Active route"
                          : "Waiting"}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {result && (
              <div className="card">
                <div className="section-label">Routing Decision</div>
                <h2>Supervisor dispatch</h2>
                <ul className="plan-list">
                  <li>
                    <div className="plan-step-header">
                      <span className="plan-step-index">1</span>
                      <span className="plan-step-name">Route</span>
                      <span className="plan-step-owner">{route}</span>
                    </div>
                    <p className="plan-step-objective">
                      {result.decision.reason}
                    </p>
                  </li>
                  <li>
                    <div className="plan-step-header">
                      <span className="plan-step-index">2</span>
                      <span className="plan-step-name">Confidence</span>
                      <span className="plan-step-owner">
                        {(confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="plan-step-objective">
                      Risk level: {riskLevel} · Approval required:{" "}
                      {requiresApproval ? "Yes" : "No"}
                    </p>
                  </li>
                  <li>
                    <div className="plan-step-header">
                      <span className="plan-step-index">3</span>
                      <span className="plan-step-name">Next step</span>
                      <span className="plan-step-owner">supervisor</span>
                    </div>
                    <p className="plan-step-objective">{nextStep}</p>
                  </li>
                </ul>
              </div>
            )}
          </section>

          <section className="column column-right">
            {navView === "requests" && (
              <>
                {result ? (
                  <>
                    <div className="card">
                      <div className="section-label">Agent Output</div>
                      <div className="output-header">
                        <div>
                          <h2>Supervisor result</h2>
                          {summaryText && (
                            <p
                              className="muted"
                              style={{ marginTop: 6, fontSize: 14 }}
                            >
                              {summaryText}
                            </p>
                          )}
                        </div>
                        <div className="badge-row">
                          <span className="badge">{route}</span>
                          <span className={`badge status-${statusLabel}`}>
                            {statusLabel.replace("_", " ")}
                          </span>
                          <span
                            className={`badge ${RISK_COLORS[riskLevel] ?? ""}`}
                          >
                            risk: {riskLevel}
                          </span>
                          <span className="badge score">
                            confidence: {(confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {deliverable ? (
                        route === "copy" ? (
                          renderCopyOutput(deliverable as Record<string, unknown>)
                        ) : route === "campaign_strategy" ? (
                          renderCampaignOutput(
                            deliverable as Record<string, unknown>
                          )
                        ) : (
                          <div className="markdown-output">
                            <ReactMarkdown>{formattedDeliverable}</ReactMarkdown>
                          </div>
                        )
                      ) : null}

                      {requiresApproval && !approved && (
                        <div className="approval-bar">
                          <div>
                            <div className="approval-title">
                              Approval required
                            </div>
                            <div className="approval-copy">
                              This run involves a high-risk action and is
                              waiting for human review before execution.
                            </div>
                          </div>
                          <button onClick={handleApprove}>Approve Run</button>
                        </div>
                      )}

                      {approved && (
                        <div className="approval-success">
                          Run approved. Supervisor status updated for review
                          handoff.
                        </div>
                      )}
                    </div>

                    <div className="card two-up">
                      <div>
                        <div className="section-label">Routing Detail</div>
                        <h2>Decision trace</h2>
                        <p className="muted">
                          <strong style={{ color: "var(--text)" }}>
                            Route:
                          </strong>{" "}
                          {route}
                        </p>
                        <p className="muted">
                          <strong style={{ color: "var(--text)" }}>
                            Reason:
                          </strong>{" "}
                          {result.decision.reason}
                        </p>
                        <p className="muted">
                          <strong style={{ color: "var(--text)" }}>
                            Risk:
                          </strong>{" "}
                          {riskLevel}
                        </p>
                        {result.decision.missing_inputs.length > 0 && (
                          <>
                            <h3>Missing Inputs</h3>
                            {result.decision.missing_inputs.map((m, i) => (
                              <p key={i} className="muted">
                                {m}
                              </p>
                            ))}
                          </>
                        )}
                      </div>

                      <div>
                        <div className="section-label">Quality Review</div>
                        <h2>Route review</h2>
                        <p>
                          <strong>Route used:</strong>{" "}
                          {result.result.route_used}
                        </p>
                        <p className="muted">
                          Approval required:{" "}
                          {requiresApproval ? "Yes" : "No"}
                        </p>
                        <p className="muted" style={{ marginTop: 12 }}>
                          <strong style={{ color: "var(--text)" }}>
                            Next step:
                          </strong>{" "}
                          {nextStep}
                        </p>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="card empty-state">
                    <div className="section-label">Run Details</div>
                    <h2>No run yet</h2>
                    <p className="muted">
                      Configure the business context and submit a request to
                      view the routing decision, structured deliverable, risk
                      classification, and approval status.
                    </p>
                  </div>
                )}
              </>
            )}

            {navView === "runs" && (
              <div className="card">
                <div className="section-label">Decision Trace</div>
                <h2>Full routing output</h2>
                {result ? (
                  <>
                    <div className="action-row">
                      <button
                        type="button"
                        onClick={() => setShowRawRun((prev) => !prev)}
                      >
                        {showRawRun ? "Show compact view" : "Show raw JSON"}
                      </button>
                    </div>
                    <div className="hubspot-action">
                      {showRawRun ? (
                        <>
                          <h3>Decision</h3>
                          <pre>{JSON.stringify(result.decision, null, 2)}</pre>
                          <h3>Result</h3>
                          <pre>{JSON.stringify(result.result, null, 2)}</pre>
                        </>
                      ) : (
                        <>
                          <h3>Decision</h3>
                          <pre>
                            {JSON.stringify(
                              {
                                route: result.decision.route,
                                confidence: result.decision.confidence,
                                reason: result.decision.reason,
                                risk_level: result.decision.risk_level,
                                requires_human_approval:
                                  result.decision.requires_human_approval,
                                missing_inputs: result.decision.missing_inputs,
                              },
                              null,
                              2
                            )}
                          </pre>
                          <h3>Deliverable Preview</h3>
                          <pre>
                            {JSON.stringify(result.result.deliverable, null, 2)}
                          </pre>
                        </>
                      )}
                    </div>
                  </>
                ) : (
                  <p className="muted">
                    Run the supervisor to see the decision trace.
                  </p>
                )}
              </div>
            )}

            {navView === "hubspot" && (
              <div className="card">
                <div className="section-label">CRM Output</div>
                <h2>CRM workflow deliverable</h2>
                {result && route === "crm_ops" ? (
                  <div className="hubspot-action">
                    <h3>Workflow Blueprint</h3>
                    <pre>
                      {JSON.stringify(
                        (deliverable as Record<string, unknown>)
                          ?.workflow_blueprint ?? deliverable,
                        null,
                        2
                      )}
                    </pre>
                    <h3>HubSpot Fields to Confirm</h3>
                    <pre>
                      {JSON.stringify(
                        (deliverable as Record<string, unknown>)
                          ?.hubspot_fields_to_confirm ?? [],
                        null,
                        2
                      )}
                    </pre>
                    <h3>Suggested Property Stamps</h3>
                    <pre>
                      {JSON.stringify(
                        (deliverable as Record<string, unknown>)
                          ?.suggested_property_stamps ?? [],
                        null,
                        2
                      )}
                    </pre>
                    <h3>QA Checklist</h3>
                    <pre>
                      {JSON.stringify(
                        (deliverable as Record<string, unknown>)
                          ?.qa_checklist ?? [],
                        null,
                        2
                      )}
                    </pre>
                  </div>
                ) : (
                  <p className="muted">
                    {result
                      ? `This run used the "${route}" route. Submit a CRM ops or HubSpot workflow request to see CRM output here.`
                      : "Run a CRM ops request to see workflow blueprint output here."}
                  </p>
                )}
              </div>
            )}

            {navView === "evaluations" && (
              <div className="card">
                <div className="section-label">Route Review</div>
                <h2>Routing evaluation</h2>
                {result ? (
                  <>
                    <div className="badge-row">
                      <span className="badge">{route}</span>
                      <span className="badge score">
                        {(confidence * 100).toFixed(0)}% confidence
                      </span>
                      <span
                        className={`badge ${RISK_COLORS[riskLevel] ?? ""}`}
                      >
                        {riskLevel} risk
                      </span>
                    </div>
                    <div
                      className="markdown-output eval-markdown"
                      style={{ marginTop: 12 }}
                    >
                      <ReactMarkdown>{`**Route:** ${route}

**Reason:** ${result.decision.reason}

**Risk level:** ${riskLevel}

**Requires approval:** ${requiresApproval ? "Yes" : "No"}

**Missing inputs:** ${
                        result.decision.missing_inputs.length > 0
                          ? result.decision.missing_inputs.join(", ")
                          : "None"
                      }`}</ReactMarkdown>
                    </div>
                  </>
                ) : (
                  <p className="muted">
                    Run the supervisor to see route evaluation.
                  </p>
                )}
              </div>
            )}

            {navView === "settings" && (
              <div className="card">
                <div className="section-label">System Config</div>
                <h2>Settings</h2>
                <p className="muted">
                  Deterministic routing mode is active. The supervisor uses a
                  keyword-based route table with 7 valid routes: crm_ops,
                  reporting, copy, campaign_strategy, research, clarify, and
                  reject.
                </p>
                <p className="muted" style={{ marginTop: 12 }}>
                  High-risk actions require human approval before execution.
                  Low and medium risk deliverables are returned immediately as
                  structured outputs.
                </p>
                <p className="muted" style={{ marginTop: 12 }}>
                  Next phase: add LLM-backed workers for copy, campaign
                  strategy, and research routes, plus LangSmith tracing per
                  node.
                </p>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;