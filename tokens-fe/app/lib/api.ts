export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type ICP = {
  industries: string[];
  company_size: string;
  geographies: string[];
  target_roles: string[];
  pain_signals: string[];
  search_queries: string[];
};

export type ProspectCandidate = {
  name: string;
  homepage_url: string;
  one_liner: string;
};

export type ProspectDossier = {
  prospect_name: string;
  homepage_url: string;
  what_they_do: string;
  decision_makers: string[];
  pain_signals_found: string[];
  fit_score: number;
  fit_rationale: string;
  citations: string[];
};

export type CallBrief = {
  prospect_name: string;
  opener: string;
  value_prop: string;
  discovery_questions: string[];
  likely_objections: string[];
  next_step_ask: string;
  citations: string[];
};

export type ProspectStatus =
  | "queued"
  | "research"
  | "ingest"
  | "analyze"
  | "brief"
  | "done"
  | "error";

export type ProspectView = {
  candidate: ProspectCandidate;
  status: ProspectStatus;
  dossier: ProspectDossier | null;
  brief: CallBrief | null;
  senso_content_ids: string[];
  error: string | null;
};

export type RunSnapshot = {
  run_id: string;
  product: string;
  step: string;
  error: string | null;
  icp: ICP | null;
  prospects: ProspectView[];
};

export type LogEvent = {
  type: "log";
  ts: number;
  level: "info" | "error";
  agent: string | null;
  prospect: string | null;
  message: string;
  meta: Record<string, unknown>;
};

export type StateEvent = {
  type: "state";
  ts?: number;
  data: RunSnapshot;
};

export type RunEvent = LogEvent | StateEvent;

export async function createRun(product: string): Promise<{ run_id: string }> {
  const r = await fetch(`${API_BASE}/runs`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ product }),
  });
  if (!r.ok) throw new Error(`createRun ${r.status}: ${await r.text()}`);
  return r.json();
}

export async function fetchRun(runId: string): Promise<RunSnapshot> {
  const r = await fetch(`${API_BASE}/runs/${runId}`);
  if (!r.ok) throw new Error(`fetchRun ${r.status}`);
  return r.json();
}

export function eventsUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/events`;
}
