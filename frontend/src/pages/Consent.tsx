import { useState } from "react";
import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Panel, Pill, useData } from "../components/ui";

export function Consent() {
  const ref = useEntrance();
  const rows = useData(api.consent, []);
  const subjects = useData(api.subjects, []);
  const [picked, setPicked] = useState<string | null>(null);
  const subject = picked ?? subjects[0] ?? "—";
  // local toggle state seeded from the (aggregate) consent rows
  const [granted, setGranted] = useState<Record<string, boolean>>({});
  const isOn = (scope: string, deflt: boolean) => granted[scope] ?? deflt;

  return (
    <div ref={ref}>
      <Panel eyebrow="DATA SUBJECT · PSEUDONYMOUS" title="" action={<Pill kind="success">pseudonymisation active · salted, re-id key vaulted</Pill>}>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {subjects.map((s) => <button key={s} className={`chip ${subject === s ? "on" : ""} mono`} onClick={() => setPicked(s)}>{s}</button>)}
        </div>
      </Panel>

      <div className="grid split" style={{ marginTop: 16 }}>
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
          <div className="faint mono" style={{ fontSize: 11, marginBottom: 12 }}>No data-subject requests on record.</div>
          <div className="muted" style={{ fontSize: 12.5, lineHeight: 1.65 }}>
            Each subject can request <b>data export</b> (Art. 20) or <b>erasure</b> (Art. 17).
            Both run through the pipeline CLI (<span className="mono">make erase PID=…</span>) and are
            written to the append-only <a className="mono" style={{ color: "var(--cyan)" }} href="/security">audit log</a>.
          </div>
          <div className="row-between" style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--line)" }}>
            <span className="muted">Active consents</span><span className="num">{rows.filter((r) => r.status === "granted").length} / {rows.length}</span>
          </div>
        </Panel>
      </div>
    </div>
  );
}
