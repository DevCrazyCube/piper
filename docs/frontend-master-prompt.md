# Master prompt — Claude design (frontend)

> Paste the block below the divider into Claude design. Direction is now **distinctive
> neon-cyber**, **every screen fully built (no stubs)**, on a **token-driven, reusable,
> responsive** system. The aesthetic POV is intentional this time — lean into it, but keep it
> legible and credible (neon is the accent, not the text).

---

You are a senior product designer **and** front-end engineer designing the dashboard for a real,
security-first data product. I want a **distinctive, neon-cyber visual identity** — memorable and
high-energy — executed as a disciplined, token-driven, fully-built system. Not a generic dark SaaS
dashboard, and not a toy: a serious security/ops product that happens to look *sharp*.

## 0. Hard rules (read first)
- **Build EVERY screen fully. No "sketch", no placeholder gray boxes, no stub panels, no "TODO".**
  Every panel has real components, real sample data, real charts, real states.
- **Token-driven**: define tokens once as variables; never hard-code values in components.
- **Reusable components**: one component library, composed into screens — no per-screen bespoke styling.
- **Responsive**: every screen works mobile → wide.
- **Accessible**: WCAG 2.1 AA text contrast, keyboard-navigable, visible focus, never color-only signaling.

## 1. The product
A dashboard for a **Responsible Learning Analytics Pipeline** — it ingests sensitive personal data
(sleep, heart rate, activity, meals) and institutional data (grades, study habits, attendance), then
cleans, normalizes, pseudonymises, encrypts, and stores it for analytics. Built **security-first and
privacy-by-design** (GDPR / ISO 27001). The dashboard is how people *see the pipeline working* and
*trust it handles data responsibly*. (Product codename in the mock: "Aegis".)

## 2. Users (role-aware views via a "Viewing as" switcher)
- **Data engineer** — pipeline runs, ingest health, data-quality issues, dead-letter/quarantine.
- **Analyst** — cross-source analytics, **aggregate-only**, never raw identities.
- **Data subject / student** — only their own data, consent state, export & erasure.
- **Auditor** — audit log, access events, anomaly flags, compliance posture.

## 3. Screens — ALL fully built
1. **Pipeline overview** — KPI row; the 8 lifecycle stages (Ingest · Transport · Store · Process ·
   Analyse · Access · Monitor · Delete) as a live flow with per-stage throughput + status; recent
   runs table; ingest-health bars.
2. **Security & audit** — KPI row; live audit-log stream (WRITE/DENY/QUERY/EXPORT/ERASURE, color-coded);
   encryption & controls panel; anomaly flags; GDPR/ISO compliance-posture cards.
3. **Pipeline runs** — full sortable/filterable **DataTable** (source, rows in→out, transformations,
   duration, outcome, quarantined), with a run-detail **drawer** and a quarantine drill-down. Real rows.
4. **Data sources & quality** — per-source freshness/lag/SLA, real charts for missing-value %, dedup
   rate, schema-harmonisation coverage, and a schema-drift alert. Real charts, not boxes.
5. **Analytics results** — aggregate-first charts (time-series, distribution/histogram, correlation),
   each labeled with cohort size and a "viewing aggregate data" affordance. Real plotted data.
6. **Consent & privacy** — per-subject consent scopes (real toggles), pseudonymisation status,
   retention countdown timers, export/erasure request queue with audit links. Real, interactive-looking.

Plus a **Design system** reference page showing the tokens.

## 4. Neon-cyber aesthetic — the POV (lean in, but disciplined)
- **Base:** deep near-black canvas with subtly layered surfaces (not flat #000) — give it depth.
- **Accent system:** one electric primary (e.g. cyan/blue or magenta/violet family — your pick, commit
  to it) plus a restrained secondary. Use accents for live/active states, focus, data-viz, key edges.
- **Glow / edge treatment:** tasteful neon — thin luminous borders, soft outer-glow on *active/live*
  elements, gradient hairlines, scanline/grid texture used **sparingly**. Glow is seasoning, not sauce:
  it marks what's live/important, it does NOT coat every element.
- **Data-viz with energy:** charts use the neon palette with gradient fills, glowing line strokes,
  crisp gridlines — expressive but precise. This is where the identity sings.
- **Typography:** a sharp modern sans for UI + a **mono** face for IDs / logs / metrics (the "ops
  terminal" feel is on-theme). Tabular figures for numeric columns.
- **Motion:** subtle, fast, purposeful — pulse on live indicators, smooth transitions; reduced-motion safe.
- **Inspiration to channel (adapt, don't copy):** a cyberpunk SOC / mission-control / observability
  console — Grafana-meets-cyberdeck — but cleaner and more premium.

## 5. Keep it READABLE and credible (don't let neon ruin it)
- **Text stays high-contrast near-white** on dark; **neon is for accents/borders/glow/data-viz, not body
  text.** Verify AA contrast for all text and meaningful UI.
- Dense operational tables/logs must stay scannable — neon highlights *signal* (status, anomalies, live),
  it doesn't decorate everything.
- It should still read as a *trustworthy security tool*, just one with a strong, deliberate identity.

## 6. Design-system tokens — MANDATORY (list explicitly with values)
- **Color** — semantic tokens: `--color-bg`, `--surface`, `--surface-raised`, `--border`, `--glow`,
  `--text`, `--text-muted`, `--primary`, `--secondary`, + status scale (`--success/--warning/--danger/--info`).
  State contrast ratios for text tokens.
- **Typography** — modular type scale (display → h1…h4 → body → small → caption) with weights/line-heights; mono face.
- **Spacing** — one scale (4px base: 4/8/12/16/24/32/48).
- **Radius** — `--radius-sm / -md / -lg / -pill` with stated usage (inputs / cards / modals / chips).
- **Elevation** — shadow/glow tokens; say what raises vs stays flat.
- **Motion** — duration + easing tokens.
- **Breakpoints** — mobile / tablet / desktop / wide as tokens.

## 7. Component library — MANDATORY, with full states
Primitives: Button (variants/sizes/states), Input/Select, Badge/Tag, **StatusPill**, Tooltip, Tabs.
Data: **DataTable** (sortable, dense + comfortable density, sticky header, pagination, empty/loading/error),
**StatCard/KPI**, **Chart** wrapper, **Timeline/Flow node** (8-stage view), **LogRow** (mono).
Shell: AppShell (collapsible nav + header + content), PageHeader, Card/Panel, Drawer/Modal, Toast.
Every component: default, hover, focus (visible ring), active, disabled, loading, error, empty.

## 8. Responsive — MANDATORY
Define breakpoints; mobile-first; layouts reflow (not just shrink). Specify: nav collapse
(sidebar → drawer/bottom-nav), dense **DataTable** on narrow screens (horizontal scroll w/ pinned key
column, or stacked cards), and how the **8-stage flow** rewraps vertically.

## 9. Privacy in the UI (non-negotiable)
Never foreground raw personal identifiers — show pseudonymous IDs + aggregates; make "viewing aggregate
data" legible; design the "no consent / access denied" state as first-class.

## 10. Deliverable
A cohesive, production-quality result: (a) the **design-system spec** (all tokens with values + usage);
(b) the **component library** with states/variants; (c) **all six screens fully built** from that system
(no stubs) plus the design-system reference page. Commit to the neon-cyber identity, keep text legible
and AA-compliant, and note the reasoning behind the key choices.
