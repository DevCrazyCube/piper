import { useState } from "react";
import { api, type Run } from "../api";
import { useEntrance } from "../lib/motion";
import { Panel, Pill, useData } from "../components/ui";

const outcome = (s: string) => (s === "success" ? "success" : s === "failed" ? "danger" : "warning");
const FILTERS = ["all", "success", "quarantine", "failed"] as const;

export function Runs() {
  const ref = useEntrance();
  const runs = useData(api.runs, []);
  const [filter, setFilter] = useState<string>("all");
  const [sel, setSel] = useState<Run | null>(null);
  const shown = runs.filter((r) => filter === "all" || r.status === filter);

  return (
    <div ref={ref}>
      <div style={{ display: "flex", gap: 8, margin: "8px 0 16px" }} data-anim>
        {FILTERS.map((f) => (
          <button key={f} className={`chip ${filter === f ? "on" : ""}`} onClick={() => setFilter(f)}>{f}</button>
        ))}
      </div>

      <Panel eyebrow="OPERATIONS" title={`Run history · ${shown.length}`}>
        <div className="table-wrap"><table className="dt">
          <thead><tr><th>Run ID</th><th>Source</th><th className="num">Rows in → out</th><th className="num">Transforms</th><th className="num">Duration</th><th>Outcome</th></tr></thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.id} onClick={() => setSel(r)} style={{ cursor: "pointer" }}>
                <td className="mono">{r.id}</td>
                <td>{r.source}</td>
                <td className="num">{r.rows_in.toLocaleString()} → {r.rows_out.toLocaleString()}</td>
                <td className="num">{r.transforms}</td>
                <td className="num">{r.duration}</td>
                <td><Pill kind={outcome(r.status)}>{r.status}</Pill></td>
              </tr>
            ))}
          </tbody>
        </table></div>
      </Panel>

      {sel && <RunDrawer run={sel} onClose={() => setSel(null)} />}
    </div>
  );
}

function RunDrawer({ run, onClose }: { run: Run; onClose: () => void }) {
  const stages = ["Ingest", "Transport", "Store", "Process", "Analyse", "Access", "Monitor", "Delete"];
  const notes = ["TLS 1.3", "in transit", "AES-256 at rest", "dedup · pseudonymise", "aggregate", "RBAC", "logged", "auto-erasure"];
  return (
    <>
      <div className="scrim" onClick={onClose} />
      <div className="drawer">
        <div className="row-between">
          <div><span className="mono" style={{ color: "var(--cyan)", fontSize: 18 }}>{run.id}</span> <Pill kind={run.status === "success" ? "success" : run.status === "failed" ? "danger" : "warning"}>{run.status}</Pill></div>
          <button className="btn" onClick={onClose}>✕</button>
        </div>
        <div className="muted" style={{ margin: "6px 0 20px" }}>{run.source} · {run.transforms} transforms · {run.duration}</div>
        <div className="eyebrow" style={{ marginBottom: 12 }}>STAGE-BY-STAGE TIMELINE</div>
        {stages.map((s, i) => (
          <div key={s} className="row-between" style={{ padding: "9px 0", borderBottom: "1px solid rgba(120,150,200,0.06)" }}>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <span style={{ width: 8, height: 8, borderRadius: 99, background: i === 3 && run.status !== "success" ? "var(--warning)" : "var(--cyan)" }} />
              <div><b style={{ fontSize: 13 }}>{s}</b><div className="faint mono" style={{ fontSize: 11 }}>{run.rows_in.toLocaleString()} → {run.rows_out.toLocaleString()} · {notes[i]}</div></div>
            </div>
            <Pill kind="success">applied</Pill>
          </div>
        ))}
        {run.quarantined > 0 && (
          <div className="glass panel" style={{ marginTop: 20, borderColor: "rgba(245,179,66,0.3)" }}>
            <div className="eyebrow" style={{ color: "var(--warning)" }}>QUARANTINE · {run.quarantined} ROWS · dead-letter</div>
            <div className="mono muted" style={{ fontSize: 12, marginTop: 10 }}>
              {run.quarantined.toLocaleString()} non-conforming row(s) routed to <span className="mono">meta.quarantine</span> for review.
            </div>
          </div>
        )}
      </div>
    </>
  );
}
