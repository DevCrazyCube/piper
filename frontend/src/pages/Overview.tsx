import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Pipeline } from "../components/Pipeline";
import { Panel, Pill, Ribbon, Sparkline, useData } from "../components/ui";

const outcome = (s: string) => (s === "success" ? "success" : s === "failed" ? "danger" : "warning");

export function Overview() {
  const ref = useEntrance();
  const o = useData(api.overview, { vitals: [], stages: [], runs: [], sources: [] });

  return (
    <div ref={ref} className="stack">
      <Ribbon vitals={o.vitals} />
      <Pipeline stages={o.stages} />

      <div className="grid cols-2" style={{ gridTemplateColumns: "1.6fr 1fr" }}>
        <Panel eyebrow="Operations" title="Recent runs" action={<a className="chip" href="/runs">View all</a>}>
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

        <Panel eyebrow="Freshness" title="Ingest health">
          {o.sources.slice(0, 5).map((s) => (
            <div key={s.name} className="row-between" style={{ padding: "12px 0", borderBottom: "1px solid var(--line)" }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13.5 }}>{s.name}</div>
                <div className="faint mono" style={{ fontSize: 11, marginTop: 2 }}>{s.last_seen} · {s.missing}% missing</div>
              </div>
              <Sparkline data={s.trend} color={s.sla === "ok" ? "#15803d" : s.sla === "risk" ? "#b45309" : "#dc2626"} />
            </div>
          ))}
        </Panel>
      </div>
    </div>
  );
}
