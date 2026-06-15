import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Pipeline } from "../components/Pipeline";
import { Panel, Pill, Sparkline, Stat, useData } from "../components/ui";

const sla = (s: string) => (s === "ok" ? "success" : s === "risk" ? "warning" : "danger");
const outcome = (s: string) => (s === "success" ? "success" : s === "failed" ? "danger" : "warning");

export function Overview() {
  const ref = useEntrance();
  const o = useData(api.overview, { vitals: [], stages: [], runs: [], sources: [] });

  return (
    <div ref={ref}>
      <div className="grid cols-6" style={{ marginTop: 4 }}>
        {o.vitals.map((v) => <Stat key={v.label} v={v} />)}
      </div>

      <div style={{ marginTop: 16 }}><Pipeline stages={o.stages} /></div>

      <div className="grid cols-2" style={{ marginTop: 16, gridTemplateColumns: "1.5fr 1fr" }}>
        <Panel eyebrow="OPERATIONS" title="Recent runs" action={<a className="chip" href="/runs">View all →</a>}>
          <table className="dt">
            <thead><tr><th>Run</th><th>Source</th><th className="num">In → Out</th><th>Outcome</th></tr></thead>
            <tbody>
              {o.runs.slice(0, 6).map((r) => (
                <tr key={r.id}>
                  <td className="mono">{r.id}</td>
                  <td>{r.source}</td>
                  <td className="num">{r.rows_in.toLocaleString()} → {r.rows_out.toLocaleString()}</td>
                  <td><Pill kind={outcome(r.status)}>{r.status}</Pill></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel eyebrow="FRESHNESS" title="Ingest health">
          {o.sources.slice(0, 5).map((s) => (
            <div key={s.name} style={{ padding: "10px 0", borderBottom: "1px solid rgba(120,150,200,0.06)" }}>
              <div className="row-between">
                <b style={{ fontSize: 13 }}>{s.name}</b>
                <span className="faint mono" style={{ fontSize: 11 }}>{s.last_seen}</span>
              </div>
              <div className="row-between" style={{ marginTop: 6 }}>
                <Sparkline data={s.trend} color={s.sla === "ok" ? "var(--success)" : s.sla === "risk" ? "var(--warning)" : "var(--danger)"} />
                <Pill kind={sla(s.sla)}>{s.missing}% miss</Pill>
              </div>
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
