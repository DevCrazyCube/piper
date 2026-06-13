# Master prompt — Claude design (frontend)

> Paste the block below the divider into Claude design. This brief gives **structure, behavior,
> toolset, and motion** — the *skeleton* of every page and component — and deliberately leaves the
> exact visual values (palette, radius, spacing numbers) to you. Direction is neon-cyber on a dark
> void with liquid-glass surfaces and lots of GSAP-driven life. Build it for real, every page.

---

You are a senior product designer **and** front-end engineer. Design and build a living, breathing
dashboard for a security-first data product. I'm giving you the **structural blueprint** of every
page and component, the **tools you can use**, and the **motion language** I want. The exact visual
choices — palette, radii, spacing, type sizes — are **yours to make**; make them deliberate and
cohesive, and craft real components, not template filler.

## 0. Hard rules (read first)
- **Build EVERY page fully and distinctly.** No stubs, no placeholder gray boxes, no "sketch" panels.
  Each page below has its **own** layout and composition — do **not** reuse one "KPI row + two panels"
  template for everything. Different pages, different shapes.
- **There is NO "design system" page in the product.** (Tokens are an internal engineering concern,
  not a screen.) The app's pages are only the six in §7.
- **Components must be designed with craft** — buttons, cards, containers, labels, inputs, tables all
  have considered anatomy and states (§8). Generic = fail.
- **Aliveness is a requirement, not a nice-to-have.** Use GSAP; motion is part of the product (§5).
- **Token discipline internally**: drive everything from variables (color/space/radius/type/glass/ease).
  Consistent radius personality. But express tokens in code/CSS — don't surface them as a page.
- **Responsive** (mobile→wide) and **accessible** (WCAG 2.1 AA text contrast, keyboard, visible focus,
  reduced-motion, never color-only). **Privacy:** never show raw identifiers — pseudonymous IDs + aggregates.

## 1. The product
"**Aegis**" — a dashboard for a Responsible Learning Analytics Pipeline. It ingests sensitive personal
data (sleep, heart rate, activity, meals) + institutional data (grades, attendance), then cleans,
normalizes, pseudonymises, encrypts, and stores it. Built security-first / privacy-by-design (GDPR,
ISO 27001). The dashboard is mission-control: *see the pipeline live, trust how it handles data.*

## 2. Users — role-aware via a "Viewing as" switcher in the header
Data engineer (runs, ingest health, quarantine) · Analyst (aggregate analytics only) · Data subject
(own data, consent, export/erasure) · Auditor (audit log, anomalies, compliance). Switching role
re-scopes what each page shows.

## 3. Toolset you can use
- **React + TypeScript**, component-driven.
- **Styling:** Tailwind **or** CSS variables — your call — but token-driven and consistent.
- **Motion:** **GSAP** (core + **ScrollTrigger**, Flip if useful) as the primary engine; CSS
  transitions only for trivial hovers. (Framer Motion acceptable as a secondary, but GSAP leads.)
- **Charts:** a real charting lib (Recharts / visx / ECharts / D3) — styled to the theme, animated draw-on.
- **Glass:** CSS `backdrop-filter` blur + layered translucency + thin luminous edges.
- **Icons:** a crisp set (Lucide / Phosphor).
- **Fonts:** a sharp modern sans for UI + a **mono** for IDs / logs / metrics.

## 4. The vibe (direction — you own the exact values)
- **Dark void base:** deep near-black with atmosphere — radial vignette / faint receding grid /
  drifting nebula glow. Surfaces float in the void; it has depth, not a flat fill.
- **Liquid glass surfaces:** panels, cards, drawers, nav are frosted translucent glass (background-blur,
  inner highlight, thin luminous edge) floating over the void. Layer translucency for depth. **Put a
  subtle scrim behind text on glass** so contrast stays AA.
- **Neon accents:** an electric palette (you choose the hues — commit to a primary + secondary) used for
  live/active states, focus, edges, glow, and data-viz. Neon = signal + accent; **text stays
  high-contrast near-white**, never neon body text.
- **Feel:** a cyberpunk SOC / mission-control console with Apple-vision liquid glass — premium, sharp,
  alive. Restraint where it counts (dense tables stay calm); energy where it sings (the live pipeline, charts).

## 5. Motion & aliveness — GSAP (this is core)
Make it feel alive without being noisy. Define **shared easing tokens** and reuse them everywhere.
- **Page entrance:** each page builds in via a GSAP timeline — regions fade+rise+settle, lists/tables
  **stagger** their rows, KPIs **count up** to value. Eases like `expo.out` / `power3.out` for entrances,
  `power2.inOut` for moves. Things **ease in, never pop**.
- **The living pipeline (signature):** on the overview, data visibly **flows** through the 8 stages —
  pulses/particles travel along the connectors stage→stage, active stages glow and breathe, throughput
  numbers tick. This is the centerpiece of "aliveness."
- **Ambient void:** slow drifting glow / aurora sweep behind content; a brief **bloom/flash** on key
  events (run completes, anomaly fires). Subtle, slow — atmosphere, not a strobe.
- **Micro-interactions:** glow-sweep across a glass edge on hover; buttons depress + ripple; status pills
  pulse when live; drawers/modals glide with eased scale+fade; toasts slide+settle.
- **Data-viz:** charts **draw on** (lines trace, areas fill, bars grow, numbers roll); live charts append
  smoothly.
- **Performance + a11y:** animate transform/opacity (GPU-friendly), no jank on dense tables; fully honor
  `prefers-reduced-motion` (kill ambient/flash + entrances, keep instant, legible states).

## 6. App shell (shared skeleton)
- **Left nav** (collapsible → icon-rail → drawer on mobile): grouped links (Operate: Overview, Runs,
  Sources, Analytics · Security: Security & audit · Privacy: Consent), with live status dots / counts.
- **Header:** page eyebrow + title (left), global search (⌘/ focus), density toggle, **"Viewing as" role
  switcher**, notifications.
- **Footer/status strip:** system health ("all systems nominal"), connection/live indicator.
- **Content region:** per-page layouts below. Keep the shell constant; vary the content shape per page.

## 7. Pages — skeletal blueprints (build all, each DISTINCT)

### 7.1 Pipeline overview — *mission control* (hero = the live pipeline)
- **Top vitals strip:** compact KPIs — rows ingested today, active runs, failed (24h), avg stage latency,
  quarantined rows, encryption coverage. Each with trend + status dot; numbers count up on load.
- **Center stage — the living 8-stage pipeline:** the dominant element, not a small strip. Eight glass
  **stage nodes** (Ingest→Delete) connected by animated flow lines; per node: throughput, status, a
  one-line control note (e.g. "TLS 1.3", "AES-256 at rest", "RBAC enforced"); active nodes glow/breathe;
  pulses travel the connectors. Clicking a stage opens its detail.
- **Bottom split:** left = **Recent runs** (live compact list: source, in→out, duration, outcome pill);
  right = **Ingest health** (per-source rows with mini sparkline/bar + freshness + a quality note).
- **Optional:** a thin **live event ticker**.

### 7.2 Pipeline runs — *operational table* (table-centric, NOT card grid)
- **Filter bar:** segmented controls (outcome: all/success/quarantine/failed), source filter, time-range,
  search. Sticky.
- **Main: a real DataTable** filling the page — columns: run id (mono), source, rows in→out, transforms,
  duration, outcome (pill), quarantined count. Sortable headers, sticky header, density toggle, pagination,
  staggered row entrance. Rows hover-highlight.
- **Row click → run-detail Drawer (side panel):** a **stage-by-stage timeline** of that run (rows in→out
  per stage, transforms applied, time per stage), errors, lineage, and a **quarantine drill-down** listing
  dead-lettered rows with raw value + failure reason + actions (reprocess / discard, audit-logged).
- States: loading (skeleton shimmer rows), empty, error.

### 7.3 Data sources & quality — *per-source grid + drill-in*
- **Source grid:** one glass card per connected source (Wearables API, LMS/grades, Attendance, Sleep
  tracker, Meals log, the datasets). Each card: type icon, freshness/last-seen, lag, **SLA state**, a mini
  health chart, and quality chips (missing %, dedup rate, harmonisation coverage). Cards glow by health.
- **Quality panel / drift alerts:** prominent schema-drift alerts (e.g. "Meals log diverged — fields
  renamed; affected rows auto-quarantined"), with link to the offending run.
- **Source click → detail:** field-level schema, quality metrics over time (charts), and for the two UCI
  datasets a **harmonisation mapping** view (how columns/scales reconcile). Real charts, not boxes.

### 7.4 Analytics results — *aggregate-first chart gallery* (privacy-forward)
- **Domain tabs/selector** (per ADR-0009): Health · Academic · Teammate cohort · Synthetic (labeled).
  Synthetic is clearly flagged as demo-only.
- **Query gallery:** a card per analytics query (Q1–Q5), each a themed **chart** (time-series, histogram,
  correlation/scatter) with title, **cohort size (n=…)**, an "aggregate only — no individual identifiable"
  badge, and the source domains it draws from.
- **Query click → detail:** large chart, controls (time range, cohort filter, binning), the
  transformation/SQL provenance, and export. Charts draw on with GSAP.

### 7.5 Security & audit — *SOC console*
- **Vitals strip:** encryption coverage, failed access (24h), open anomalies, audit events (24h).
- **Center: live Audit log stream** — mono **LogRows** color-coded by action (WRITE/READ/QUERY/DENY/
  EXPORT/ERASURE), columns: time, action, resource, actor (pseudonymous svc/usr id), result pill. Filter
  chips (ALL/DENY/EXPORT/ERASURE), "LIVE" indicator, new rows slide in.
- **Right rail:** **Encryption & controls** (at rest AES-256-GCM, in transit TLS 1.3, key rotation
  countdown, pseudonymisation active) + **Anomaly flags** (severity-tagged cards: off-hours bulk read,
  repeated denied access…).
- **Bottom: Compliance posture** — GDPR/ISO control cards (Art.32/25/5/17, ISO A.9/A.12/A.16…) each with
  pass / needs-attention status and a one-line evidence note.

### 7.6 Consent & privacy — *subject-centric*
- **Subject selector** (pseudonymous IDs only).
- **Consent scopes:** a row/toggle per data category (sleep, heart rate, activity, meals, grades,
  attendance) — individually grant/revoke, each change audit-logged; show lawful basis.
- **Pseudonymisation status** + **retention timers:** per-category countdown to scheduled auto-deletion.
- **Request queue:** data-subject requests — **export (Art.20)** and **erasure (Art.17)** — with status
  (pending/completed), SLA, and a link to the audit entry.
- **First-class "no consent / access denied" state** for scopes the viewer can't see.

## 8. Component kit — design with craft (anatomy + states + motion)
Build a reusable library; compose pages from it; no per-screen bespoke styling. For each, design the
**anatomy, all states, and its motion** (you choose the exact look):
- **Button** — variants (primary/secondary/ghost/danger), sizes, with icon; states: default/hover/focus
  (visible ring)/active(press)/loading/disabled. Consider a subtle glow/sweep on primary.
- **Card / Panel (liquid glass)** — header (title + eyebrow + action slot), body, optional footer; raised
  vs flat; loading/empty/error variants; hover lift/glow.
- **Label / Badge / StatusPill** — semantic status colors, dot/icon, sizes; pulse when "live".
- **Input / Select / SegmentedControl / FilterChip** — states incl. focus glow, error, disabled.
- **DataTable** — sortable header, sticky header, dense/comfortable density, zebra/hover, pagination,
  selection, skeleton-loading, empty, error; staggered row entrance.
- **Drawer / Modal / Toast** — eased glide/scale entrances; backdrop; focus trap.
- **StatCard / KPI** — value (count-up), label, trend, status dot, optional sparkline.
- **StageNode + FlowConnector** — the pipeline node (status, throughput, glow/breathe) and the animated
  connector (traveling pulses).
- **Chart wrapper** — line/area/bar/histogram/scatter, themed, draw-on animation, tooltip, legend, empty.
- **LogRow** — mono, action-colored, time + resource + actor + result; new-row slide-in.
- **ConsentToggle, CountdownTimer, Tabs, Tooltip, EmptyState, LoadingState (shimmer), ErrorState.**

## 9. Engineering discipline (internal, not a page)
Token-driven (color/space/radius/type/glass/ease as variables); one component library reused
everywhere; consistent radius personality; responsive reflow (nav collapse, dense tables → horizontal
scroll with pinned key column or stacked cards, 8-stage flow rewraps vertically); WCAG 2.1 AA, keyboard,
visible focus, reduced-motion; privacy by default (pseudonymous + aggregate).

## 10. Deliverable
All six pages in §7, fully built and visually distinct, composed from the §8 component kit, with the
neon-cyber / dark-void / liquid-glass identity and GSAP-driven aliveness throughout. Commit to a
deliberate, cohesive palette and component design of your own; keep text legible and AA; make it feel
alive. No design-system page, no stubs.
