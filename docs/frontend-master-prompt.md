# Master prompt — Claude design (frontend)

> Paste the block below the divider into Claude design. It specifies the product, the users, the
> functional views, and the **engineering rigor** of the design system (tokens, radius scale,
> component reuse, responsive behavior, states) — while leaving the actual *aesthetic values* for
> the model to invent and justify. The discipline is mandated; the look is open.

---

You are a senior product designer **and** front-end engineer designing the dashboard for a real,
security-first data product. I'm giving you the product, the users, the views, and a strict set of
**design-system rules**. Invent the visual language yourself, but express it as a disciplined,
reusable, token-driven system — not one-off screens.

## 1. The product
A dashboard for a **Responsible Learning Analytics Pipeline** — a system that ingests sensitive
personal data (sleep, heart rate, activity, meals) and institutional data (grades, study habits,
attendance), then cleans, normalizes, pseudonymises, encrypts, and stores it for analytics, built
**security-first and privacy-by-design** (GDPR / ISO 27001 aligned). The dashboard is how people
*see the pipeline working* and *trust it handles data responsibly*.

## 2. Users (design for these distinct roles, with role-aware views)
- **Data engineer** — pipeline runs, ingest health, data-quality issues, errors/dead-letter queue.
- **Analyst** — cross-source analytics results, **aggregate-only**, never raw identities.
- **Data subject / student** — only their own data, consent state, export & erasure requests.
- **Auditor** — audit log, access events, anomaly flags, compliance posture.

## 3. Views to design (priority order)
1. **Pipeline overview** — the 8 lifecycle stages (Ingest · Transport · Store · Process · Analyse ·
   Access · Monitor · Delete) as a live flow with per-stage status, throughput, failures.
2. **Security & audit** — audit log stream, access events, anomaly flags, encryption/control status,
   GDPR-article / control compliance summary.
3. **Pipeline runs** — run history: source, rows in/out, transformations, duration, outcome, quarantined rows.
4. **Data sources & quality** — connected sources, freshness, missing-value / dedup / harmonisation signals.
5. **Analytics results** — query outputs as charts (time-series, distributions, correlations), aggregate-first.
6. **Consent & privacy** — per-subject consent scopes, pseudonymisation status, retention timers, export/erasure.

(Deliver 1 and 2 fully; sketch the rest reusing the same system.)

## 4. Design-system rules — MANDATORY

Produce an explicit, **token-driven** system. Define tokens once as variables and reference them
everywhere; no hard-coded magic values in components.

- **Color** — semantic tokens, not raw hex in components: `--color-bg`, `--surface`,
  `--surface-raised`, `--border`, `--text`, `--text-muted`, `--primary`, plus a full **status scale**
  (`--success / --warning / --danger / --info`) since this is an operational tool. Define for dark
  mode (required); light mode optional. State exact contrast ratios — meet **WCAG 2.1 AA**.
- **Typography** — one type scale (e.g. a modular ratio): define steps (display → h1…h4 → body →
  small → caption), weights, line-heights, and a mono face for IDs / logs / numbers. Tabular figures
  for any numeric column.
- **Spacing** — one spacing scale (e.g. a 4px base: 4/8/12/16/24/32/48). All padding/margins/gaps
  reference it.
- **Radius** — define a **radius scale** (`--radius-sm / -md / -lg / -pill`) and state where each is
  used (inputs vs cards vs chips vs avatars) and apply it **consistently** — pick a deliberate radius
  personality and never deviate ad hoc.
- **Elevation / shadows** — a small set of elevation tokens; say what raises (modals, popovers, raised
  surfaces) vs what stays flat.
- **Borders & dividers** — token-driven width + color; consistent rules for separating dense data.
- **Motion** — duration + easing tokens; purposeful, fast, reduced-motion-respecting; no decorative animation.

## 5. Component reuse — MANDATORY
Design a **component library**, then compose screens from it. No bespoke per-screen styling. At minimum:
- Primitives: Button (variants/sizes/states), Input/Select, Badge/Tag, **StatusPill**, Tooltip, Tabs.
- Data: **DataTable** (sortable, dense + comfortable density, sticky header, pagination, empty/loading/error),
  **StatCard / KPI**, Chart wrapper, **Timeline/Flow node** (for the 8-stage view), **LogRow** (mono).
- Shell: AppShell (nav + header + content), PageHeader, Card/Panel, Drawer/Modal, Toast.
Specify each component's **states**: default, hover, focus (visible focus ring — keyboard-navigable),
active, disabled, loading, error, empty. Document variants and the props/tokens they consume.

## 6. Responsive design — MANDATORY
- Define **breakpoints** (e.g. mobile / tablet / desktop / wide) as tokens.
- Mobile-first; layouts must reflow, not just shrink. Specify how the **AppShell nav** collapses
  (sidebar → drawer/bottom-nav), how **dense DataTables** behave on narrow screens (horizontal scroll
  with pinned key column, or card/stacked rows), and how the **8-stage flow** rewraps vertically.
- Fluid type/spacing where it helps; never let dense operational data become unusable on smaller widths.

## 7. Hard product constraints (non-negotiable)
- **Trust over flash.** A security/compliance tool must read as credible, precise, and calm — not
  gimmicky. Reject any choice that trades credibility for spectacle.
- **Information-dense but legible** — design for scanning, hierarchy, dense tables/charts without clutter.
- **Honest states** — empty, loading, error, "no consent / access denied" are first-class, not afterthoughts.
- **Privacy by default** — never foreground raw personal identifiers; show pseudonymous IDs +
  aggregates; make "you are viewing aggregate data" legible.
- **Accessible** — WCAG 2.1 AA, keyboard navigable, visible focus, never color-only signaling.

## 8. Aesthetic — your call (but justify it)
Invent the full visual language and explain in 2–3 lines *why* it suits a trustworthy security
product. A stakeholder floated a "modern dark / neon" direction — treat it as **optional inspiration
you may adopt, adapt, or reject**, with a one-line reason. Restraint is welcome; coherence is required.

## 9. Deliverable
A cohesive, production-quality result: (a) the **design-system spec** — all tokens (color, type,
spacing, radius, elevation, motion, breakpoints) listed with values + usage rules; (b) the
**component library** with states/variants; (c) the **Pipeline overview** and **Security & audit**
screens fully realized from that system, with the other views sketched. Show the tokens explicitly so
the system is reusable and auditable, and note the reasoning behind the key choices.
