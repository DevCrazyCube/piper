/* Typed API client. Talks to the FastAPI read endpoints. There is NO mock data:
   if a call fails the UI shows an empty/disconnected state — never fabricated numbers. */

const BASE = (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";

export type Tone = "ok" | "warn" | "bad";
export interface Vital { label: string; value: string; unit?: string; sub?: string; tone?: Tone }
export interface Stage { n: string; name: string; thru: string; note: string; status: "live" | "ok" | "idle" }
export interface Run { id: string; source: string; status: "success" | "quarantine" | "failed"; rows_in: number; rows_out: number; transforms: number; duration: string; quarantined: number }
export interface Source { name: string; kind: string; last_seen: string; sla: "ok" | "risk" | "drift"; missing: number; dedup: number; harmonised: number; trend: number[] }
export interface Query { key: string; title: string; domain: "health" | "academic" | "synthetic"; kind: "line" | "bar" | "scatter"; n: number; data: number[]; tags: string[] }
export interface AuditEvent { t: string; action: string; object: string; actor: string; result: "ok" | "denied" | "pending" | "warn" }
export interface Anomaly { title: string; detail: string; severity: "HIGH" | "MED" | "LOW" }
export interface Control { control: string; article: string; status: "pass" | "attention"; note: string }
export interface ConsentRow { scope: string; status: "granted" | "revoked"; basis: string; subjects: number }
export interface SecuritySummary { encryption_coverage: number; failed_access_24h: number; audit_events_24h: number; open_anomalies: number }
export interface Overview { vitals: Vital[]; stages: Stage[]; runs: Run[]; sources: Source[] }

async function get<T>(path: string, empty: T): Promise<T> {
  try {
    const r = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(8000) });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return (await r.json()) as T;
  } catch (e) {
    // No mock fallback — surface emptiness honestly rather than inventing data.
    console.warn(`[api] GET ${path} failed; rendering empty state:`, e);
    return empty;
  }
}

export const api = {
  overview: () => get<Overview>("/v1/overview", { vitals: [], stages: [], runs: [], sources: [] }),
  runs: () => get<Run[]>("/v1/runs", []),
  sources: () => get<Source[]>("/v1/sources", []),
  analytics: () => get<Query[]>("/v1/analytics", []),
  audit: () => get<AuditEvent[]>("/v1/security/audit", []),
  anomalies: () => get<Anomaly[]>("/v1/security/anomalies", []),
  controls: () => get<Control[]>("/v1/security/compliance", []),
  securitySummary: () => get<SecuritySummary>("/v1/security/summary",
    { encryption_coverage: 0, failed_access_24h: 0, audit_events_24h: 0, open_anomalies: 0 }),
  consent: () => get<ConsentRow[]>("/v1/consent", []),
  subjects: () => get<string[]>("/v1/consent/subjects", []),
};
