import { useState } from "react";
import { api } from "../api";
import { useEntrance } from "../lib/motion";
import { Bars, LineChart, Scatter, useData } from "../components/ui";

const DOMAINS = ["all", "health", "academic"] as const;

export function Analytics() {
  const ref = useEntrance();
  const queries = useData(api.analytics, []);
  const [domain, setDomain] = useState<string>("all");
  const shown = queries.filter((q) => domain === "all" || q.domain === domain);

  return (
    <div ref={ref}>
      <div className="row-between" style={{ margin: "8px 0 16px" }} data-anim>
        <div style={{ display: "flex", gap: 8 }}>
          {DOMAINS.map((d) => <button key={d} className={`chip ${domain === d ? "on" : ""}`} onClick={() => setDomain(d)}>{d}</button>)}
        </div>
        <span className="pill"><span className="dot" />aggregate only · no individual is identifiable</span>
      </div>

      <div className="grid cols-3">
        {shown.map((q) => (
          <div key={q.key} className="glass panel" data-anim>
            <div className="row-between" style={{ marginBottom: 4 }}>
              <span className="mono" style={{ color: "var(--cyan)" }}>{q.key}</span>
              <span className="tag">k≥3 · aggregate</span>
            </div>
            <h2 style={{ fontSize: 14, margin: "4px 0 14px", minHeight: 38 }}>{q.title}</h2>
            {q.kind === "line" ? <LineChart data={q.data} />
              : q.kind === "scatter" ? <Scatter data={q.data} />
                : <Bars data={q.data} color={q.domain === "academic" ? "var(--violet)" : "var(--cyan)"} />}
            <div className="row-between" style={{ marginTop: 12 }}>
              <span className={`tag ${q.domain}`}>{q.domain}</span>
              <span className="num faint">n = {q.n.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
