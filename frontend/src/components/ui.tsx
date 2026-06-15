import { type ReactNode, useEffect, useState } from "react";
import {
  Area, AreaChart, Bar as RBar, BarChart, CartesianGrid, Cell,
  ResponsiveContainer, Scatter as RScatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import { useCountUp } from "../lib/motion";
import type { Vital } from "../api";

const ACCENT = "#4338ca";
const ACCENT2 = "#0e8f86";

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
        <div className="row-between" style={{ marginBottom: 18 }}>
          <div>
            {eyebrow && <div className="eyebrow">{eyebrow}</div>}
            {title && <h2 style={{ marginTop: eyebrow ? 4 : 0 }}>{title}</h2>}
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

function Value({ v }: { v: Vital }) {
  const isNum = !Number.isNaN(num(v.value));
  const dec = v.value.includes(".") ? (v.value.split(".")[1]?.length ?? 0) : 0;
  const counted = useCountUp(isNum ? num(v.value) : 0, dec);
  return <>{isNum ? counted : v.value}{v.unit && <span className="unit">{v.unit}</span>}</>;
}

/** One calm KPI ribbon (hairline-separated) — replaces a row of boxes. */
export function Ribbon({ vitals }: { vitals: Vital[] }) {
  return (
    <div className="glass ribbon" data-anim>
      {vitals.map((v) => (
        <div key={v.label} className="kpi">
          <div className="label">{v.label}</div>
          <div className="value"><Value v={v} /></div>
          {v.sub && <div className={`sub ${v.tone === "bad" ? "bad" : v.tone === "warn" ? "warn" : ""}`}>{v.sub}</div>}
        </div>
      ))}
    </div>
  );
}

export function Stat({ v }: { v: Vital }) {
  const dot = v.tone === "bad" ? "var(--danger)" : v.tone === "warn" ? "var(--warning)" : "var(--success)";
  return (
    <div className="glass stat" data-anim>
      <div className="label">{v.label}<span style={{ width: 6, height: 6, borderRadius: 99, background: dot }} /></div>
      <div className="value"><Value v={v} /></div>
      {v.sub && <div className={`sub ${v.tone === "bad" ? "bad" : v.tone === "warn" ? "warn" : ""}`}>{v.sub}</div>}
    </div>
  );
}

/* ---------- charts (Recharts, themed minimal) ---------- */
const Tip = ({ active, payload }: any) =>
  active && payload?.length ? <div className="tip">{(+payload[0].value).toLocaleString()}</div> : null;

export function LineChart({ data, color = ACCENT }: { data: number[]; color?: string }) {
  const d = data.map((v, i) => ({ i, v }));
  return (
    <div className="chart" style={{ height: 150 }}>
      <ResponsiveContainer>
        <AreaChart data={d} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
          <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.18} /><stop offset="100%" stopColor={color} stopOpacity={0} /></linearGradient></defs>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="i" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
          <YAxis tickLine={false} axisLine={false} width={36} tick={{ fontSize: 10 }} />
          <Tooltip content={<Tip />} cursor={{ stroke: color, strokeOpacity: 0.3 }} />
          <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill="url(#g)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Bars({ data, labels, color = ACCENT }: { data: number[]; labels?: string[]; color?: string }) {
  const d = data.map((v, i) => ({ name: labels?.[i] ?? String(i + 1), v }));
  return (
    <div className="chart" style={{ height: 150 }}>
      <ResponsiveContainer>
        <BarChart data={d} margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="name" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
          <YAxis tickLine={false} axisLine={false} width={36} tick={{ fontSize: 10 }} />
          <Tooltip content={<Tip />} cursor={{ fill: "rgba(67,56,202,0.06)" }} />
          <RBar dataKey="v" radius={[4, 4, 0, 0]}>
            {d.map((_, i) => <Cell key={i} fill={color} fillOpacity={0.55 + 0.45 * (d[i].v / Math.max(...data))} />)}
          </RBar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Scatter({ data, color = ACCENT2 }: { data: number[]; color?: string }) {
  const d = data.map((v, i) => ({ x: i + 1, y: v }));
  return (
    <div className="chart" style={{ height: 150 }}>
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 6, right: 8, bottom: 0, left: -18 }}>
          <CartesianGrid />
          <XAxis type="number" dataKey="x" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
          <YAxis type="number" dataKey="y" tickLine={false} axisLine={false} width={36} tick={{ fontSize: 10 }} />
          <Tooltip content={<Tip />} cursor={{ strokeOpacity: 0.2 }} />
          <RScatter data={d} fill={color} fillOpacity={0.75} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Sparkline({ data, color = ACCENT }: { data: number[]; color?: string }) {
  const d = data.map((v, i) => ({ i, v }));
  const id = `sp-${color.replace(/[^a-z0-9]/gi, "")}`;
  return (
    <AreaChart data={d} width={116} height={32} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
      <defs><linearGradient id={id} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.2} /><stop offset="100%" stopColor={color} stopOpacity={0} /></linearGradient></defs>
      <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.6} fill={`url(#${id})`} />
    </AreaChart>
  );
}

export function Bar({ pct, color }: { pct: number; color?: string }) {
  return <div className="bar-track"><div className="bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: color }} /></div>;
}
