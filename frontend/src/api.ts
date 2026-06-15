/* Typed API client. Tries the FastAPI read endpoints; falls back to realistic mock data
   (same shapes) so the dashboard always renders for a demo even without the backend. */

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
export interface Overview { vitals: Vital[]; stages: Stage[]; runs: Run[]; sources: Source[] }

async function get<T>(path: string, fallback: T): Promise<T> {
  try {
    const r = await fetch(`${BASE}${path}`, { signal: AbortSignal.timeout(2500) });
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as T;
  } catch {
    return fallback;
  }
}

/* ---------- mock data (mirrors the real schema/queries) ---------- */
const STAGES: Stage[] = [
  { n: "01", name: "Ingest", thru: "2,840", note: "validated · idempotent", status: "live" },
  { n: "02", name: "Transport", thru: "2,838", note: "TLS 1.3", status: "live" },
  { n: "03", name: "Store", thru: "2,791", note: "AES-256 at rest", status: "live" },
  { n: "04", name: "Process", thru: "2,791", note: "clean · pseudonymise", status: "live" },
  { n: "05", name: "Analyse", thru: "9.8k", note: "aggregate only", status: "ok" },
  { n: "06", name: "Access", thru: "RBAC", note: "row-level security", status: "ok" },
  { n: "07", name: "Monitor", thru: "live", note: "0 anomalies", status: "live" },
  { n: "08", name: "Delete", thru: "2", note: "verified erasure", status: "idle" },
];
const RUNS: Run[] = [
  { id: "run_9241", source: "Wearables API", status: "quarantine", rows_in: 4200, rows_out: 4178, transforms: 6, duration: "3m 12s", quarantined: 22 },
  { id: "run_9240", source: "LMS · grades", status: "success", rows_in: 1044, rows_out: 1044, transforms: 4, duration: "1m 04s", quarantined: 0 },
  { id: "run_9239", source: "Attendance", status: "success", rows_in: 4266, rows_out: 4266, transforms: 5, duration: "0m 38s", quarantined: 0 },
  { id: "run_9238", source: "Sleep tracker", status: "success", rows_in: 4299, rows_out: 4299, transforms: 9, duration: "2m 51s", quarantined: 0 },
  { id: "run_9237", source: "Meals log", status: "failed", rows_in: 19000, rows_out: 0, transforms: 0, duration: "0m 12s", quarantined: 0 },
  { id: "run_9236", source: "UCI · student-perf", status: "success", rows_in: 1044, rows_out: 662, transforms: 3, duration: "0m 09s", quarantined: 0 },
  { id: "run_9235", source: "Open Food Facts", status: "success", rows_in: 50000, rows_out: 50000, transforms: 2, duration: "1m 34s", quarantined: 0 },
];
const SOURCES: Source[] = [
  { name: "Wearables API", kind: "stream", last_seen: "12s ago", sla: "ok", missing: 0.3, dedup: 99.7, harmonised: 100, trend: [3, 5, 4, 6, 5, 7, 8] },
  { name: "LMS · grades", kind: "batch", last_seen: "4m ago", sla: "ok", missing: 1.1, dedup: 100, harmonised: 98, trend: [4, 4, 5, 6, 6, 7, 7] },
  { name: "Attendance", kind: "batch", last_seen: "38m ago", sla: "risk", missing: 4.7, dedup: 99.1, harmonised: 94, trend: [8, 6, 5, 4, 4, 3, 3] },
  { name: "Sleep tracker", kind: "stream", last_seen: "21s ago", sla: "ok", missing: 0.8, dedup: 99.9, harmonised: 100, trend: [3, 4, 5, 5, 6, 7, 8] },
  { name: "Meals log", kind: "stream", last_seen: "2m ago", sla: "drift", missing: 6.2, dedup: 97.4, harmonised: 71, trend: [6, 5, 5, 4, 3, 3, 2] },
  { name: "UCI · student-perf", kind: "dataset", last_seen: "static", sla: "ok", missing: 0, dedup: 100, harmonised: 100, trend: [5, 6, 5, 7, 6, 7, 6] },
  { name: "Open Food Facts", kind: "dataset", last_seen: "static", sla: "ok", missing: 12, dedup: 100, harmonised: 95, trend: [5, 5, 6, 6, 7, 7, 8] },
];
const VITALS: Vital[] = [
  { label: "Rows ingested · today", value: "1.28", unit: "M", sub: "+8.4% vs avg", tone: "ok" },
  { label: "Active runs", value: "12", sub: "3 streaming" },
  { label: "Failed · 24h", value: "1", sub: "meals: schema drift", tone: "bad" },
  { label: "Avg stage latency", value: "214", unit: "ms", sub: "p95 410ms" },
  { label: "Quarantined rows", value: "22", sub: "awaiting review", tone: "warn" },
  { label: "Encryption coverage", value: "100", unit: "%", sub: "transit + at rest", tone: "ok" },
];
const QUERIES: Query[] = [
  { key: "Q1", title: "Average & range of daily active minutes", domain: "health", kind: "bar", n: 15, data: [180, 240, 210, 320, 260, 290, 251, 300, 220, 270], tags: ["health"] },
  { key: "Q2", title: "Weekly activity-minutes cohort trend", domain: "health", kind: "line", n: 15, data: [42, 64, 87, 93, 92, 88, 95, 106, 87, 86, 95, 88], tags: ["health"] },
  { key: "Q3", title: "Study time vs academic outcome", domain: "academic", kind: "bar", n: 662, data: [0.527, 0.564, 0.624, 0.611], tags: ["academic"] },
  { key: "Q4", title: "Sleep vs activity correlation (cohort)", domain: "health", kind: "scatter", n: 15, data: [70, 65, 80, 55, 90, 60, 75, 50, 85, 68, 72, 58, 88, 62, 78], tags: ["health"] },
  { key: "Q5", title: "Cross-institutional grade distribution", domain: "academic", kind: "bar", n: 793, data: [0.563, 0.647], tags: ["academic"] },
];
const AUDIT: AuditEvent[] = [
  { t: "18:40:14", action: "WRITE", object: "store/raw/wearables", actor: "svc:ingest", result: "ok" },
  { t: "18:40:11", action: "DENY", object: "analytics/raw/identities", actor: "usr:8f3c", result: "denied" },
  { t: "18:40:07", action: "WRITE", object: "store/norm/attendance", actor: "svc:store", result: "ok" },
  { t: "18:39:56", action: "QUERY", object: "analytics/aggregate/sleep_grades", actor: "svc:analyse", result: "ok" },
  { t: "14:31:40", action: "READ", object: "audit/log", actor: "usr:auditor-2", result: "ok" },
  { t: "14:30:12", action: "ERASE", object: "subject/self · Art.17", actor: "usr:0a2d", result: "pending" },
  { t: "14:29:03", action: "EXPORT", object: "subject/self/data · Art.20", actor: "usr:1b9e", result: "ok" },
];
const ANOMALIES: Anomaly[] = [
  { title: "Off-hours bulk read", detail: "svc:export-01 · 03:14 · 4.1k rows", severity: "MED" },
  { title: "Repeated denied access", detail: "usr:0a2d · 7× raw/identities", severity: "LOW" },
];
const CONTROLS: Control[] = [
  { control: "Security of processing", article: "GDPR Art.32", status: "pass", note: "AES-256-GCM + TLS planned" },
  { control: "Protection by design", article: "GDPR Art.25", status: "pass", note: "pseudonymisation default" },
  { control: "Data minimisation", article: "GDPR Art.5", status: "attention", note: "meals_log retains 2 fields" },
  { control: "Right to erasure", article: "GDPR Art.17", status: "pass", note: "cascade + receipt" },
  { control: "Access control", article: "ISO A.9", status: "pass", note: "non-superuser role + RLS" },
  { control: "Operations security", article: "ISO A.12", status: "attention", note: "TLS termination planned" },
];
const CONSENT: ConsentRow[] = [
  { scope: "sleep", status: "granted", basis: "Art.6(1)(a)", subjects: 14 },
  { scope: "heart_rate", status: "granted", basis: "Art.6(1)(a)", subjects: 13 },
  { scope: "activity", status: "granted", basis: "Art.6(1)(a)", subjects: 15 },
  { scope: "meals", status: "revoked", basis: "Art.6(1)(a)", subjects: 9 },
  { scope: "grades", status: "granted", basis: "Art.6(1)(e)", subjects: 662 },
  { scope: "attendance", status: "granted", basis: "Art.6(1)(e)", subjects: 131 },
];

export const api = {
  overview: () => get<Overview>("/v1/overview", { vitals: VITALS, stages: STAGES, runs: RUNS, sources: SOURCES }),
  runs: () => get<Run[]>("/v1/runs", RUNS),
  sources: () => get<Source[]>("/v1/sources", SOURCES),
  analytics: () => get<Query[]>("/v1/analytics", QUERIES),
  audit: () => get<AuditEvent[]>("/v1/security/audit", AUDIT),
  anomalies: () => get<Anomaly[]>("/v1/security/anomalies", ANOMALIES),
  controls: () => get<Control[]>("/v1/security/compliance", CONTROLS),
  consent: () => get<ConsentRow[]>("/v1/consent", CONSENT),
};
