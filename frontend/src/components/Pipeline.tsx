import type { Stage } from "../api";

/** The signature element: the responsible-pipeline lifecycle as a left-to-right rail.
    The 01–08 numbering is real — it's the order data moves through. Each node names the
    one security/privacy control that applies at that stage. Live segments flow (CSS). */
export function Pipeline({ stages }: { stages: Stage[] }) {
  return (
    <div className="glass panel" data-anim>
      <div className="row-between" style={{ marginBottom: 22 }}>
        <div>
          <div className="eyebrow">Lifecycle</div>
          <h2 style={{ marginTop: 4 }}>A control at every stage</h2>
        </div>
        <span className="pill live"><span className="dot" />live</span>
      </div>
      <div className="rail">
        {stages.map((s) => (
          <div key={s.n} className={`node ${s.status === "live" ? "live" : ""}`}>
            <div className="num">{s.n}</div>
            <div className="nm">{s.name}</div>
            <div className="thru">{s.thru}<span className="u"> r/s</span></div>
            <div className="ctl">{s.note}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
