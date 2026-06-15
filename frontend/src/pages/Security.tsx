import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Panel, Pill, Stat, useData } from "../components/ui";

const resultPill = (r: string) => (r === "ok" ? "success" : r === "denied" ? "danger" : r === "warn" ? "warning" : "");

export function Security() {
  const ref = useEntrance();
  const audit = useData(api.audit, []);
  const anomalies = useData(api.anomalies, []);
  const controls = useData(api.controls, []);
  const sum = useData(api.securitySummary, { encryption_coverage: 100, failed_access_24h: 0, audit_events_24h: 0, open_anomalies: 0 });
  const pass = controls.filter((c) => c.status === "pass").length;

  return (
    <div ref={ref}>
      <div className="grid cols-4" style={{ marginTop: 4 }}>
        <Stat v={{ label: "Encryption coverage", value: String(sum.encryption_coverage), unit: "%", sub: "verified at rest", tone: "ok" }} />
        <Stat v={{ label: "Failed access · 24h", value: String(sum.failed_access_24h), sub: sum.failed_access_24h ? "all denied & logged" : "none denied", tone: sum.failed_access_24h ? "warn" : "ok" }} />
        <Stat v={{ label: "Open anomalies", value: String(sum.open_anomalies), sub: sum.open_anomalies ? "awaiting review" : "none open", tone: sum.open_anomalies ? "warn" : "ok" }} />
        <Stat v={{ label: "Audit events · 24h", value: sum.audit_events_24h.toLocaleString(), sub: "append-only ledger", tone: "ok" }} />
      </div>

      <div className="grid split" style={{ marginTop: 16 }}>
        <Panel eyebrow="IMMUTABLE" title="Audit log stream" action={<span className="pill live">LIVE</span>}>
          <div className="log">
            <div className="row" style={{ color: "var(--text-faint)", fontSize: 10 }}><span>TIME</span><span>ACTION</span><span>RESOURCE</span><span>ACTOR</span><span>RESULT</span></div>
            {audit.map((e, i) => (
              <div className="row" key={i}>
                <span className="t">{e.t}</span>
                <span className={`act-${e.action}`}>{e.action}</span>
                <span className="muted">{e.object}</span>
                <span className="faint">{e.actor}</span>
                <span><Pill kind={resultPill(e.result)}>{e.result}</Pill></span>
              </div>
            ))}
          </div>
        </Panel>

        <div>
          <Panel eyebrow="" title="Encryption & controls">
            {[["At rest", "AES-256-GCM"], ["In transit", "TLS 1.3 (planned)"], ["Key separation", "HKDF per-purpose"], ["Pseudonymisation", "active"]].map(([k, v]) => (
              <div key={k} className="row-between" style={{ padding: "9px 0", borderBottom: "1px solid rgba(120,150,200,0.06)" }}>
                <span className="muted">{k}</span><span className="mono" style={{ color: "var(--cyan)", fontSize: 12 }}>{v}</span>
              </div>
            ))}
          </Panel>
          <div style={{ height: 16 }} />
          <Panel eyebrow={`${anomalies.length} OPEN`} title="Anomaly flags">
            {anomalies.map((a) => (
              <div key={a.title} style={{ padding: "8px 0 8px 12px", borderLeft: `2px solid ${a.severity === "HIGH" ? "var(--danger)" : a.severity === "MED" ? "var(--warning)" : "var(--cyan)"}`, marginBottom: 8 }}>
                <div className="row-between"><b style={{ fontSize: 13 }}>{a.title}</b><span className="tag">{a.severity}</span></div>
                <div className="faint mono" style={{ fontSize: 11 }}>{a.detail}</div>
              </div>
            ))}
          </Panel>
        </div>
      </div>

      <div className="section-title">Compliance posture · GDPR · ISO 27001 — {pass}/{controls.length} passing</div>
      <div className="grid cols-3">
        {controls.map((c) => (
          <div key={c.control} className="glass panel" data-anim style={{ borderColor: c.status === "attention" ? "rgba(245,179,66,0.3)" : undefined }}>
            <div className="row-between"><span className="mono" style={{ color: "var(--cyan)", fontSize: 12 }}>{c.article}</span><Pill kind={c.status === "pass" ? "success" : "warning"}>{c.status}</Pill></div>
            <b style={{ display: "block", margin: "8px 0 4px", fontSize: 14 }}>{c.control}</b>
            <div className="faint mono" style={{ fontSize: 11 }}>{c.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
