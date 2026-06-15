import { useState } from "react";
import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Panel, Pill, useData } from "../components/ui";

const SUBJECTS = ["subj_7c4e", "subj_a912", "subj_3f08", "subj_e651"];

export function Consent() {
  const ref = useEntrance();
  const rows = useData(api.consent, []);
  const [subject, setSubject] = useState(SUBJECTS[0]);
  // local toggle state seeded from the (aggregate) consent rows
  const [granted, setGranted] = useState<Record<string, boolean>>({});
  const isOn = (scope: string, deflt: boolean) => granted[scope] ?? deflt;

  return (
    <div ref={ref}>
      <Panel eyebrow="DATA SUBJECT · PSEUDONYMOUS" title="" action={<Pill kind="success">pseudonymisation active · salted, re-id key vaulted</Pill>}>
        <div style={{ display: "flex", gap: 8 }}>
          {SUBJECTS.map((s) => <button key={s} className={`chip ${subject === s ? "on" : ""} mono`} onClick={() => setSubject(s)}>{s}</button>)}
        </div>
      </Panel>

      <div className="grid cols-2" style={{ marginTop: 16, gridTemplateColumns: "1.4fr 1fr" }}>
        <Panel eyebrow={`CONSENT SCOPES · ${subject}`} title="Data categories & lawful basis">
          {rows.map((r) => {
            const on = isOn(r.scope, r.status === "granted");
            return (
              <div key={r.scope} className="row-between" style={{ padding: "12px 0", borderBottom: "1px solid rgba(120,150,200,0.06)" }}>
                <div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <b style={{ textTransform: "capitalize" }}>{r.scope.replace("_", " ")}</b>
                    <Pill kind={on ? "success" : "danger"}>{on ? "granted" : "revoked"}</Pill>
                  </div>
                  <div className="faint mono" style={{ fontSize: 11, marginTop: 3 }}>
                    Consent ({r.basis}) · {on ? "auto-delete in 540d" : "⏳ erasure scheduled · 30d"}
                  </div>
                </div>
                <div className={`toggle ${on ? "on" : ""}`} role="switch" aria-checked={on}
                  onClick={() => setGranted((g) => ({ ...g, [r.scope]: !on }))} />
              </div>
            );
          })}
          <div className="faint mono" style={{ fontSize: 11, marginTop: 12 }}>
            Revoking a scope deletes its curated data (scoped erasure) — not just a flag.
          </div>
        </Panel>

        <Panel eyebrow="SUBJECT REQUESTS" title="Art. 20 / Art. 17">
          {[
            { k: "Export (Art.20)", id: "dsr_0481", st: "completed", sla: "2/30 days" },
            { k: "Erasure (Art.17)", id: "dsr_0479", st: "pending", sla: "5/30 days" },
            { k: "Export (Art.20)", id: "dsr_0472", st: "pending", sla: "11/30 days" },
          ].map((q) => (
            <div key={q.id} className="glass" style={{ padding: 14, marginBottom: 10, borderRadius: "var(--r-sm)" }}>
              <div className="row-between"><b style={{ fontSize: 13 }}>{q.k}</b><Pill kind={q.st === "completed" ? "success" : "warning"}>{q.st}</Pill></div>
              <div className="faint mono" style={{ fontSize: 11, marginTop: 4 }}>{q.id} · SLA {q.sla} · <a style={{ color: "var(--cyan)" }} href="/security">view audit entry</a></div>
            </div>
          ))}
          <div className="row-between" style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
            <span className="muted">Active consents</span><span className="num">{rows.filter((r) => r.status === "granted").length} / {rows.length}</span>
          </div>
        </Panel>
      </div>
    </div>
  );
}
