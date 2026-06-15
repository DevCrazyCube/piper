import { usePipelinePulses } from "../lib/motion";
import type { Stage } from "../api";

/** The living 8-stage pipeline — the hero of the overview. Active nodes glow; pulses
    travel the connectors (GSAP). Laid out 4×2 so the grid stays balanced. */
export function Pipeline({ stages }: { stages: Stage[] }) {
  usePipelinePulses([stages.length]);
  return (
    <div className="glass panel" data-anim>
      <div className="row-between" style={{ marginBottom: 16 }}>
        <div>
          <div className="eyebrow">LIVE PIPELINE</div>
          <h2 style={{ margin: "4px 0 0" }}>Ingest → Transport → Store → Process → Analyse → Access → Monitor → Delete</h2>
        </div>
        <span className="pill live">LIVE</span>
      </div>
      <div className="pipe">
        {stages.map((s, i) => (
          <div key={s.n} className={`stage ${s.status === "live" ? "live" : ""}`}>
            <div className="row-between">
              <span className="n">{s.n}</span>
              <span className={`pill ${s.status === "live" ? "live" : s.status === "idle" ? "" : "success"}`} style={{ fontSize: 9, padding: "1px 7px" }}>
                {s.status.toUpperCase()}
              </span>
            </div>
            <div className="name">{s.name}</div>
            <div className="thru">{s.thru} <span className="faint" style={{ fontSize: 11 }}>r/s</span></div>
            <div className="note">{s.note}</div>
            {/* connectors except at the end of each row (cols of 4) */}
            {i % 4 !== 3 && i !== stages.length - 1 && (
              <div className="flow"><span className="pulse" /></div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
