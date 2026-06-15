import { type ReactNode, useEffect, useState } from "react";
import { useCountUp } from "../lib/motion";
import type { Vital } from "../api";

export function useData<T>(fn: () => Promise<T>, initial: T): T {
  const [d, setD] = useState<T>(initial);
  useEffect(() => {
    let on = true;
    fn().then((v) => on && setD(v));
    return () => { on = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  return d;
}

export function Panel({ eyebrow, title, action, children, className = "" }: {
  eyebrow?: string; title?: string; action?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <div className={`glass panel ${className}`} data-anim>
      {(title || action) && (
        <div className="row-between" style={{ marginBottom: 16 }}>
          <div>
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            {title && <h2 style={{ margin: eyebrow ? "4px 0 0" : 0 }}>{title}</h2>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function Pill({ kind = "", children }: { kind?: string; children: ReactNode }) {
  return <span className={`pill ${kind}`}><span className="dot" />{children}</span>;
}

const num = (s: string) => parseFloat(s.replace(/,/g, ""));

export function Stat({ v }: { v: Vital }) {
  const isNum = !Number.isNaN(num(v.value));
  const dec = v.value.includes(".") ? (v.value.split(".")[1]?.length ?? 0) : 0;
  const counted = useCountUp(isNum ? num(v.value) : 0, dec);
  const dotColor = v.tone === "bad" ? "var(--danger)" : v.tone === "warn" ? "var(--warning)" : "var(--success)";
  return (
    <div className="glass stat" data-anim>
      <div className="label">{v.label}<span style={{ width: 7, height: 7, borderRadius: 99, background: dotColor }} /></div>
      <div className="value">{isNum ? counted : v.value}{v.unit && <span className="unit">{v.unit}</span>}</div>
      {v.sub && <div className={`sub ${v.tone === "bad" ? "bad" : v.tone === "warn" ? "warn" : ""}`}>{v.sub}</div>}
    </div>
  );
}

/* ---------- charts (hand-built SVG, with axes) ---------- */
const W = 320, H = 120, PAD = 22;

export function LineChart({ data, color = "var(--cyan)" }: { data: number[]; color?: string }) {
  const max = Math.max(...data), min = Math.min(...data, 0);
  const x = (i: number) => PAD + (i / (data.length - 1)) * (W - PAD * 2);
  const y = (v: number) => H - PAD - ((v - min) / (max - min || 1)) * (H - PAD * 2);
  const pts = data.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="line chart">
        {[0, 0.5, 1].map((t) => <line key={t} className="gridline" x1={PAD} x2={W - PAD} y1={PAD + t * (H - PAD * 2)} y2={PAD + t * (H - PAD * 2)} />)}
        <line className="axis" x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} />
        <polygon fill={color} opacity="0.12" points={`${PAD},${H - PAD} ${pts} ${W - PAD},${H - PAD}`} />
        <polyline fill="none" stroke={color} strokeWidth="2" points={pts} style={{ filter: `drop-shadow(0 0 4px ${color})` }} />
        <text className="tick" x={PAD} y={12}>{max.toFixed(0)}</text>
        <text className="tick" x={PAD} y={H - PAD + 12}>{min.toFixed(0)}</text>
      </svg>
    </div>
  );
}

export function Bars({ data, labels, color = "var(--cyan)" }: { data: number[]; labels?: string[]; color?: string }) {
  const max = Math.max(...data);
  const bw = (W - PAD * 2) / data.length;
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="bar chart">
        <line className="axis" x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} />
        {data.map((v, i) => {
          const h = (v / max) * (H - PAD * 2);
          return <rect key={i} x={PAD + i * bw + bw * 0.18} y={H - PAD - h} width={bw * 0.64} height={h}
            rx="3" fill={color} opacity={0.55 + 0.45 * (v / max)} />;
        })}
        {labels?.map((l, i) => <text key={i} className="tick" x={PAD + i * bw + bw / 2} y={H - PAD + 12} textAnchor="middle">{l}</text>)}
        <text className="tick" x={PAD} y={12}>{max.toFixed(max < 5 ? 2 : 0)}</text>
      </svg>
    </div>
  );
}

export function Scatter({ data, color = "var(--violet)" }: { data: number[]; color?: string }) {
  const max = Math.max(...data), min = Math.min(...data);
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="scatter plot">
        <line className="axis" x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} />
        <line className="axis" x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} />
        {data.map((v, i) => {
          const cx = PAD + ((i + 0.5) / data.length) * (W - PAD * 2);
          const cy = H - PAD - ((v - min) / (max - min || 1)) * (H - PAD * 2);
          return <circle key={i} cx={cx} cy={cy} r="3.5" fill={color} opacity="0.8" style={{ filter: `drop-shadow(0 0 3px ${color})` }} />;
        })}
      </svg>
    </div>
  );
}

export function Sparkline({ data, color = "var(--success)" }: { data: number[]; color?: string }) {
  const max = Math.max(...data), min = Math.min(...data);
  const w = 120, h = 30;
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * h}`).join(" ");
  return <svg width={w} height={h} style={{ display: "block" }}><polyline fill="none" stroke={color} strokeWidth="1.8" points={pts} /></svg>;
}

export function Bar({ pct, color }: { pct: number; color?: string }) {
  return <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: color }} /></div>;
}
