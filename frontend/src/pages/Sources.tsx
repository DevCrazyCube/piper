import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Bar, Panel, Pill, Sparkline, useData } from "../components/ui";

const slaPill = (s: string) => (s === "ok" ? "success" : s === "risk" ? "warning" : "danger");
const slaText = (s: string) => (s === "ok" ? "within SLA" : s === "risk" ? "at risk" : "schema drift");

export function Sources() {
  const ref = useEntrance();
  const sources = useData(api.sources, []);
  const drift = sources.filter((s) => s.sla === "drift");

  return (
    <div ref={ref}>
      {drift.length > 0 && (
        <Panel eyebrow="SCHEMA DRIFT & SLA ALERTS" title={`${drift[0].name} — schema drift`} className="glow"
          action={<a className="chip" href="/runs">View offending run →</a>}>
          <div className="muted">Fields renamed (meal_type, kcal→calories); affected rows auto-quarantined. Harmonisation coverage dropped to {drift[0].harmonised}%.</div>
        </Panel>
      )}

      <div className="section-title">{sources.length} ingest streams & datasets</div>
      <div className="grid cols-4">
        {sources.map((s) => (
          <div key={s.name} className={`glass panel ${s.sla === "drift" ? "" : ""}`} data-anim style={{ borderColor: s.sla !== "ok" ? (s.sla === "risk" ? "rgba(245,179,66,0.3)" : "rgba(245,96,77,0.3)") : undefined }}>
            <div className="row-between">
              <div><b>{s.name}</b><div className="faint mono" style={{ fontSize: 10, textTransform: "uppercase" }}>{s.kind}</div></div>
              <Pill kind={slaPill(s.sla)}>{slaText(s.sla)}</Pill>
            </div>
            <div style={{ margin: "14px 0" }}><Sparkline data={s.trend} color={s.sla === "ok" ? "var(--success)" : s.sla === "risk" ? "var(--warning)" : "var(--danger)"} /></div>
            {[["missing", s.missing], ["dedup", s.dedup], ["harmonised", s.harmonised]].map(([k, v]) => (
              <div key={k as string} style={{ marginBottom: 8 }}>
                <div className="row-between" style={{ fontSize: 11 }}><span className="faint mono" style={{ textTransform: "uppercase" }}>{k}</span><span className="num">{v}%</span></div>
                <Bar pct={k === "missing" ? (v as number) * 4 : (v as number)} color={k === "missing" && (v as number) > 5 ? "var(--danger)" : undefined} />
              </div>
            ))}
            <div className="faint mono" style={{ fontSize: 11, marginTop: 10 }}>{s.last_seen}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
