import { useEffect, useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { api, type Counts } from "./api";
import { Overview } from "./pages/Overview";
import { Runs } from "./pages/Runs";
import { Sources } from "./pages/Sources";
import { Analytics } from "./pages/Analytics";
import { Security } from "./pages/Security";
import { Consent } from "./pages/Consent";

interface RouteMeta { path: string; label: string; group: string; eyebrow: string; title: string; countKey?: keyof Counts }
const ROUTES: RouteMeta[] = [
  { path: "/", label: "Overview", group: "Operate", eyebrow: "MISSION CONTROL", title: "Pipeline overview" },
  { path: "/runs", label: "Runs", group: "Operate", eyebrow: "OPERATIONS", title: "Pipeline runs", countKey: "runs" },
  { path: "/sources", label: "Sources", group: "Operate", eyebrow: "INGEST", title: "Data sources & quality", countKey: "sources" },
  { path: "/analytics", label: "Analytics", group: "Operate", eyebrow: "INSIGHTS", title: "Analytics results" },
  { path: "/security", label: "Security & audit", group: "Security", eyebrow: "TRUST", title: "Security & audit", countKey: "anomalies" },
  { path: "/consent", label: "Consent", group: "Privacy", eyebrow: "PRIVACY", title: "Consent & data rights", countKey: "consent" },
];
/** Polls /healthz so the header can show whether data is live or the API is down
    (no more guessing whether numbers are real). */
function useApiStatus(): boolean | null {
  const [ok, setOk] = useState<boolean | null>(null);
  useEffect(() => {
    const base = (import.meta as any).env?.VITE_API_BASE ?? "http://localhost:8000";
    let alive = true;
    const ping = () =>
      fetch(`${base}/healthz`, { signal: AbortSignal.timeout(4000) })
        .then((r) => alive && setOk(r.ok))
        .catch(() => alive && setOk(false));
    ping();
    const id = setInterval(ping, 10000);
    return () => { alive = false; clearInterval(id); };
  }, []);
  return ok;
}

export default function App() {
  const loc = useLocation();
  const apiOk = useApiStatus();
  const [counts, setCounts] = useState<Counts>({ runs: 0, sources: 0, anomalies: 0, consent: 0 });
  useEffect(() => { api.counts().then(setCounts); }, [loc.pathname]);
  const meta = ROUTES.find((r) => r.path === loc.pathname) ?? ROUTES[0];
  const groups = [...new Set(ROUTES.map((r) => r.group))];

  return (
    <>
      <div className="void" />
      <div className="shell">
        <nav className="nav">
          <div className="brand">
            <div className="logo" />
            <div><b>Piper</b><small>RLA PIPELINE</small></div>
          </div>
          {groups.map((g) => (
            <div key={g}>
              <div className="nav-group">{g}</div>
              {ROUTES.filter((r) => r.group === g).map((r) => (
                <NavLink key={r.path} to={r.path} end={r.path === "/"} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
                  <span>{r.label}</span>
                  {r.path === "/"
                    ? <span className="count">{apiOk === false ? "off" : "live"}</span>
                    : r.countKey && counts[r.countKey] > 0
                      ? <span className="count">{counts[r.countKey]}</span>
                      : null}
                </NavLink>
              ))}
            </div>
          ))}
          <div className="nav-foot"><span className="dot">●</span> Piper · local stack<br />RLA pipeline · v0.1</div>
        </nav>

        <div className="main">
          <header className="topbar">
            <div>
              <div className="eyebrow">{meta.eyebrow}</div>
              <h1>{meta.title}</h1>
            </div>
            <div className="spacer" />
            <div className="search"><span>⌕</span> Search runs, IDs, controls… <span className="faint mono">⌘/</span></div>
            <span className={`pill ${apiOk === false ? "danger" : apiOk ? "success" : ""}`} title="Live API connection">
              <span className="dot" />{apiOk === false ? "API offline" : apiOk ? "live data" : "connecting…"}
            </span>
          </header>
          <main className="content">
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/runs" element={<Runs />} />
              <Route path="/sources" element={<Sources />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/security" element={<Security />} />
              <Route path="/consent" element={<Consent />} />
            </Routes>
          </main>
        </div>
      </div>
    </>
  );
}
