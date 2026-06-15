import { useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import { Overview } from "./pages/Overview";
import { Runs } from "./pages/Runs";
import { Sources } from "./pages/Sources";
import { Analytics } from "./pages/Analytics";
import { Security } from "./pages/Security";
import { Consent } from "./pages/Consent";

interface RouteMeta { path: string; label: string; group: string; eyebrow: string; title: string; count?: string }
const ROUTES: RouteMeta[] = [
  { path: "/", label: "Overview", group: "Operate", eyebrow: "MISSION CONTROL", title: "Pipeline overview", count: "live" },
  { path: "/runs", label: "Runs", group: "Operate", eyebrow: "OPERATIONS", title: "Pipeline runs", count: "12" },
  { path: "/sources", label: "Sources", group: "Operate", eyebrow: "INGEST", title: "Data sources & quality", count: "7" },
  { path: "/analytics", label: "Analytics", group: "Operate", eyebrow: "INSIGHTS", title: "Analytics results" },
  { path: "/security", label: "Security & audit", group: "Security", eyebrow: "TRUST", title: "Security & audit", count: "2" },
  { path: "/consent", label: "Consent", group: "Privacy", eyebrow: "PRIVACY", title: "Consent & data rights", count: "1" },
];
const ROLES = ["Data engineer", "Analyst", "Data subject", "Auditor"];

export default function App() {
  const [role, setRole] = useState(ROLES[0]);
  const loc = useLocation();
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
                  {r.count && <span className={`count ${r.count === "live" ? "" : ""}`}>{r.count}</span>}
                </NavLink>
              ))}
            </div>
          ))}
          <div className="nav-foot"><span className="dot">●</span> All systems nominal<br />uptime 99.98% · 6 nodes</div>
        </nav>

        <div className="main">
          <header className="topbar">
            <div>
              <div className="eyebrow">{meta.eyebrow}</div>
              <h1>{meta.title}</h1>
            </div>
            <div className="spacer" />
            <div className="search"><span>⌕</span> Search runs, IDs, controls… <span className="faint mono">⌘/</span></div>
            <div className="role">
              <span className="faint" style={{ fontSize: 11 }}>VIEWING AS</span>
              <select value={role} onChange={(e) => setRole(e.target.value)}>
                {ROLES.map((r) => <option key={r}>{r}</option>)}
              </select>
            </div>
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
