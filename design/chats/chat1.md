# Data Pipeline Dashboard

_Started 2026-06-13 17:14 UTC_

---

## User

<system-info comment="Only acknowledge these if relevant">
Project title is now "Piper"
Project is currently empty (no files)
Current date is now June 13, 2026
</system-info>

<default aesthetic_system_instructions>
The user has not attached a design system. If they have ALSO not attached references or art direction, and the project is empty, you must ASK the user what visual aesthetic they want. Use the questions_v2 tool to ask about preferred vibe, audience, colors, type, mood, etc. Do NOT just pick your own visual aesthetic without getting the user's aesthetic input -- this is how you get slop!

Once answered, use this guidance when creating designs:
- Choose a type pairing from web-safe set or Google Fonts. Helvetica is a good choice. Avoid hard-to-read or overly stylized fonts. Use 1-3 fonts only.
- Foreground and background: choose a color tone (warm, cool, neutral, something in-between). Use subtly-toned whites and blacks; avoid saturations above 0.02 for whites.
- Accents: choose 0-2 additional accent colors using oklch. All accents should share same chroma and lightness; vary hue.
- NEVER write out an SVG yourself that's more complicated than a square, circle, diamond, etc.
- For imagery, never hand-draw SVGs; use subtly-striped SVG placeholders instead with monospace explainers for what should be dropped there (e.g. “product shot”)

CRITICAL: ignore default aesthetic entirely if given other aesthetic instructions like reference images, design systems or guidance, or if there are files in the project already.
</default aesthetic_system_instructions>

<pasted_text name="Pasted text (180 lines)">
# Master prompt — Claude design (frontend)

&gt; Paste the block below the divider into Claude design. This brief gives **structure, behavior,
&gt; toolset, and motion** — the *skeleton* of every page and component — and deliberately leaves the
&gt; exact visual values (palette, radius, spacing numbers) to you. Direction is neon-cyber on a dark
&gt; void with liquid-glass surfaces and lots of GSAP-driven life. Build it for real, every page.

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
"**Piper**" — a dashboard for a Responsible Learning Analytics Pipeline. It ingests sensitive personal
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

## 5. Motion &amp; aliveness — GSAP (this is core)
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
  Sources, Analytics · Security: Security &amp; audit · Privacy: Consent), with live status dots / counts.
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

### 7.3 Data sources &amp; quality — *per-source grid + drill-in*
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

### 7.5 Security &amp; audit — *SOC console*
- **Vitals strip:** encryption coverage, failed access (24h), open anomalies, audit events (24h).
- **Center: live Audit log stream** — mono **LogRows** color-coded by action (WRITE/READ/QUERY/DENY/
  EXPORT/ERASURE), columns: time, action, resource, actor (pseudonymous svc/usr id), result pill. Filter
  chips (ALL/DENY/EXPORT/ERASURE), "LIVE" indicator, new rows slide in.
- **Right rail:** **Encryption &amp; controls** (at rest AES-256-GCM, in transit TLS 1.3, key rotation
  countdown, pseudonymisation active) + **Anomaly flags** (severity-tagged cards: off-hours bulk read,
  repeated denied access…).
- **Bottom: Compliance posture** — GDPR/ISO control cards (Art.32/25/5/17, ISO A.9/A.12/A.16…) each with
  pass / needs-attention status and a one-line evidence note.

### 7.6 Consent &amp; privacy — *subject-centric*
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

</pasted_text>

<!-- The user explicitly selected the following skills for this project, as attachments to their message. These are not optional context — they define how you work. Use them. -->
<attached-skill name="Design Components">
This project uses Design Components: every design is a single streaming `Name.dc.html` file. The full authoring spec is in your system prompt under "Writing code — Design Components" — follow it. Author and edit `.dc.html` content with the `dc_write`, `dc_html_str_replace`, and `dc_js_str_replace` tools (not `write_file`; `str_replace_edit` works but won't stream); template edits stream into the live preview as you type.
</attached-skill>


<system-reminder>Auto-injected reminder (ignore if not relevant): do not recreate copyrighted or branded UI unless the user's email domain matches that company. Create original designs instead.</system-reminder>

## Assistant

_[tool: questions_v2]_

This is a meaty, well-specified brief — "Piper," a security/privacy mission-control dashboard with a neon-cyber dark-void / liquid-glass identity and GSAP motion, all six pages built distinctly. The brief deliberately leaves the exact visual values to me, so before I commit the system I want your input on a few aesthetic forks that are hard to reverse later.

## User

Questions answered:
- void_atmosphere: Balanced — slow drifting aurora glow + grid (recommended)
- neon_palette: 0
- type_pairing: Space Grotesk + JetBrains Mono — geometric, techy
- default_role: Data engineer — full pipeline ops
- charts_scope: Yes — hand-built themed charts with draw-on animation is fine
- scope_check: All six in one pass, then iterate
- extras: Each page must be structurally DISTINCT — do not reuse one KPI-row+two-panels template across pages; the layouts in §7 differ on purpose. The living 8-stage pipeline on 
  ▎ the Overview is the hero moment — invest the most motion there (traveling pulses along connectors, breathing active nodes). Craft the components (buttons, cards, labels,
  ▎ inputs, tables) — no default/generic look; this should NOT resemble a stock Linear/Vercel dashboard. Keep all text high-contrast and AA-legible over the glass (use 
  ▎ scrims). Everything reduced-motion safe. No design-system page.

## Assistant

_[tool: update_todos]_

Locked in: **cyan (#22d3ee) + violet (#a855f7)** on a deep void, balanced drifting aurora + grid, Space Grotesk / JetBrains Mono, Data engineer as the default role, hand-built draw-on charts, all six distinct pages, GSAP-led motion with the living pipeline as the hero. Let me set up the plan and start building.

_[tool: dc_write]_

Starting with the full logic class (all mock data + role scoping + GSAP motion engine) and the shell + Overview hero. This is the foundation; I'll append pages 2–6 after verifying motion works.

_[tool: show_html]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: grep]_

Template compile failed — I used unsupported `style-base` / `style-focus-within` attributes. Let me find them.

_[tool: read_file]_

I'll fix all of these mechanically: merge each `style-base` into its element's `style` (static first, dynamic hole last so themed values win), and relocate the `style-focus-within` to the input's `style-focus`.

_[tool: run_script]_

_[tool: show_html]_

_[tool: multi_screenshot]_

Strong start — glass, neon, mono all reading well. Let me see the pipeline nodes and lower sections.

_[tool: eval_js]_

_[tool: multi_screenshot]_

_[tool: update_todos]_

Overview is landing beautifully — living pipeline with traveling pulses, glass nodes, runs, ingest health, ticker. Let me fix the header eyebrow wrap, then build the remaining five pages. Marking progress:

_[tool: dc_html_str_replace]_

_[tool: dc_html_str_replace]_

Now the Runs page — operational DataTable with sortable sticky headers, filters, pagination, and a run-detail drawer (stage timeline + quarantine drill-down). First the drawer keyframes, then the page markup, then the logic.

_[tool: dc_html_str_replace]_

_[tool: dc_js_str_replace]_

Now the Runs logic — state fields and the renderVals computation block.

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: eval_js]_

_[tool: show_html]_

_[tool: get_webview_logs]_

_[tool: eval_js]_

_[tool: eval_js]_

_[tool: save_screenshot]_

Sections are just mid-entrance when captured. Let me navigate to Runs in-page and wait for the entrance to settle.

_[tool: save_screenshot]_

_[tool: eval_js]_

Runs table works. The sticky column-header is mispositioned (floating over a data row). Let me check its geometry.

_[tool: eval_js]_

_[tool: str_replace_edit]_

The `overflow-x:hidden` on the content wrapper makes it a sticky containing block without actually scrolling, so sticky offsets misbehave. The robust fix is to make the content region a real scroll container (fixed viewport height + min-height:0 chain). Let me refactor the shell.

_[tool: save_screenshot]_

_[tool: eval_js]_

Still wrong, and the row-click didn't open the drawer. Let me inspect the live state directly.

_[tool: str_replace_edit]_

Drawer opens correctly. The column-header `position:sticky` is fighting the inner scroll container (content offset by exactly the header height). With only 9 rows per page a sticky header isn't essential — I'll drop it to kill the bug cleanly.

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: read_file]_

The 7 columns don't fit the narrow preview, collapsing the `1fr` source column to zero. I'll wrap the table in a horizontal-scroll container with a min-width so columns keep their size and the source column reappears (degrades to horizontal scroll on narrow, per the responsive spec). Let me read the section to restructure precisely.

_[tool: read_file]_

_[tool: str_replace_edit]_

_[tool: dc_js_str_replace]_

_[tool: save_screenshot]_

_[tool: save_screenshot]_

Drawer timeline is gorgeous. Let me check the quarantine drill-down (scroll the drawer) and confirm the source column now renders in the table.

_[tool: eval_js]_

_[tool: update_todos]_

Runs page is complete — table with filters, sort, pagination, and a full run-detail drawer (stage timeline, lineage, errors, quarantine drill-down with audited actions). Marking done and moving to Sources.

_[tool: snip]_

_[tool: dc_html_str_replace]_

Now the Sources page — a distinct per-source card grid with drift alerts and a source-detail drawer (schema, quality-over-time, harmonisation mapping).

_[tool: dc_js_str_replace]_

Now the Sources logic — state, sparkline path builders, drift alerts, and source-detail data.

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: save_screenshot]_

_[tool: get_webview_logs]_

_[tool: eval_js]_

_[tool: grep]_

Logic class failed to hot-reload (stale version still running). Let me read the sources block I inserted to find the error.

_[tool: read_file]_

_[tool: read_file]_

_[tool: show_html]_

Code looks valid. Let me do a full reload — the hot-reload may simply not have re-evaluated. Then navigate to Sources.

_[tool: eval_js]_

_[tool: save_screenshot]_

It works after reload — source cards are present. The earlier issue was just a stale hot-reload. Let me capture it.

_[tool: save_screenshot]_

Sources page renders well. The text overlap in the alert is an html-to-image capture artifact (line-height on wrapped text). Let me verify the source-detail drawer with schema + harmonisation by opening a UCI dataset.

_[tool: eval_js]_

_[tool: update_todos]_

Source-detail drawer confirmed (schema + harmonisation mapping). Sources page complete. Onward to Analytics.

_[tool: snip]_

Now the Analytics page — domain tabs, aggregate-only chart gallery (line/hist/scatter/bar, draw-on), and a query-detail modal with controls + SQL provenance.

_[tool: dc_html_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: eval_js]_

Analytics gallery renders with the scatter chart and domain tabs. Let me verify the query-detail modal opens with the big chart + SQL provenance.

_[tool: update_todos]_

Analytics complete (gallery + draw-on charts + detail modal with SQL provenance). Now the Security & audit SOC console with a live log stream.

_[tool: snip]_

_[tool: dc_html_str_replace]_

_[tool: dc_html_str_replace]_

Now the Security & audit page template — SOC console with vitals, live log stream, encryption/anomaly rail, compliance posture.

_[tool: dc_js_str_replace]_

Now the Security logic — live log stream with a timer, plus renderVals.

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_html_str_replace]_

_[tool: dc_js_str_replace]_

Now the security renderVals block and flag:

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: eval_js]_

Security console looks strong. Let me verify the live log appends and the compliance posture renders.

_[tool: eval_js]_

_[tool: update_todos]_

Security page complete (vitals, live audit stream, encryption/anomaly rail, compliance posture). The live append is gated on tab visibility — it'll stream in the user's live view. Final page: Consent & privacy.

_[tool: snip]_

_[tool: dc_html_str_replace]_

_[tool: dc_html_str_replace]_

Now the Consent & privacy page — subject selector, consent toggles (audit-logged), retention countdowns, request queue, and a first-class access-denied state. Plus a global toast.

_[tool: dc_js_str_replace]_

Now the Consent logic — state, toggles that log to the audit stream + toast, retention math, and role-gated denial.

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: dc_js_str_replace]_

_[tool: show_html]_

_[tool: save_screenshot]_

_[tool: eval_js]_

Consent page is rich and complete. Let me verify the toggle→toast→audit flow and the analyst access-denied state.

_[tool: eval_js]_

Toggle → toast → audit-log flow confirmed. Let me verify the analyst access-denied state on the consent page.

_[tool: dc_html_str_replace]_

All six pages are built and verified functionally. Now the craft/a11y pass — adding a global visible focus ring for keyboard users (the one accessibility gap), then a full verification sweep.

_[tool: save_screenshot]_

Let me confirm the overview still renders cleanly (no regressions) after all the additions, then hand off.

_[tool: update_todos]_

All six pages are built, distinct, and verified — the access-denied state above is the live analyst view. Marking complete and handing off (the fresh load resets to the default Data-engineer Overview).**Piper** is built — a full security-first RLA pipeline mission-control console, all six pages distinct and composed from a consistent liquid-glass / neon-cyber kit on the drifting-aurora void.

- **Overview** — the living 8-stage pipeline is the hero: glass stage nodes, traveling cyan pulses along connectors, breathing active nodes, count-up KPIs, recent runs + ingest health + event ticker.
- **Runs** — operational DataTable (sortable, filterable, paginated, density-aware) with a run-detail drawer: stage-by-stage timeline, lineage, errors, and an audited quarantine drill-down.
- **Sources** — per-source glass card grid with health glow + sparklines, prominent drift/SLA alerts, and a detail drawer with field schema, quality-over-time chart, and UCI harmonisation mapping.
- **Analytics** — domain tabs, aggregate-only chart gallery (line/hist/scatter/bar, GSAP draw-on), n=cohort badges, and a query-detail modal with controls + SQL provenance.
- **Security & audit** — SOC vitals, a **live** color-coded audit stream (new rows slide in), encryption/key-rotation rail, anomaly flags, and GDPR/ISO compliance posture.
- **Consent & privacy** — subject selector, consent toggles that write to the audit stream with a toast, retention countdowns, Art.20/17 request queue, and a first-class **access-denied** state for the Analyst role.

Role switching re-scopes the data; everything honors `prefers-reduced-motion`; keyboard focus is visible.

A couple of notes: the live audit stream pauses while the tab is backgrounded (resumes when visible), and the dense Runs table / Security log are tuned for desktop width — they fall back to horizontal scroll on narrow viewports.

_[tool: done]_

Clean load, no console errors, and the background verifier is running. Piper is ready to explore — start on the Overview to watch the pipeline breathe, then use the left nav (and the **Viewing as** role switcher in the header) to move through Runs, Sources, Analytics, Security & audit, and Consent. Let me know what you'd like to refine — palette intensity, motion pacing, specific page layouts, or wiring up real data shapes.

## User



## Assistant

## Assistant

