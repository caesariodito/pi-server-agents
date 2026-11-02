# implementation-plan.json schema

One JSON object renders one self-contained implementation-plan review page. See `example.json` for a complete source.

Prose fields are escaped. Backticks render code and `**text**` renders bold. URLs accept relative paths, `#`, `http:`, `https:`, and `file:`; unsafe schemes fail validation.

## Top level

Required fields:

| Field | Shape | Rule |
|---|---|---|
| `title` | string | Page title. |
| `doc_type` | string | Exactly `implementation-plan`. |
| `status` | string | `draft`, `in-review`, `active`, `shipped`, `done`, or `dropped`. `shipped`: every DoD item is verified. `done`: outcome targets were checked, met or explicitly accepted as missed. Builder rejects `shipped` or `done` while any DoD item is open. |
| `version` | string/number | Plan version. |
| `updated` | `YYYY-MM-DD` | Last material update. |
| `owner` | string | Accountable owner. |
| `reviewers` | string[] | May be empty. |
| `links` | object | Label-to-URL map. |
| `current_phase` | integer | Must equal one phase `number`. |
| `tagline` | string | One-line outcome. |
| `summary` | object | Fields: `building`, `so_that`, `done_when`, `biggest_risk`, `now`. |
| `business_context` | object | Fields below. |
| `goals_scope` | object | Goal, outcomes, definition of done, and scope; fields below. |
| `system_shape` | object | Fields below; link the paired technical spec when one exists. |
| `modules` | array | Workstream records below. |
| `decisions` | array | Decision records below. Preserve superseded decisions. |
| `phases` | array | Phase records below. |
| `risks_assumptions` | object | Fields below. |
| `rollout_rollback` | object | Fields below. |
| `observability` | object | Outcome metrics; fields below. |
| `open_questions` | array | Question records below. |
| `change_log` | array | Newest first. |

Optional top-level fields:

| Field | Shape | Meaning |
|---|---|---|
| `key` | string | Unique `localStorage` key. Defaults from title/version/updated. Change each review round. |
| `answers_filename` | string | Download name. Defaults to `<slug>-answers.md`. |
| `lang` | string | HTML language. Default `en`. |
| `guides` | object | Authoring guide text keyed by section: `summary`, `business_context`, `goals_scope`, `system_shape`, `modules`, `decisions`, `phases`, `risks_assumptions`, `rollout_rollback`, `observability`, `open_questions`, `change_log`. Hidden until toolbar toggle. |

Optional `links["diagram reference"]` points to derived `./diagrams.md` and appears under sidebar Links. Detailed Mermaid sources remain in Markdown, not this JSON schema.

## ID registry

Use only these IDs. Every ID belongs to one owning document. The builder rejects unregistered prefixes and malformed IDs everywhere IDs appear: record `id` fields, `affects`, `covers`, `tracks_goal`, and `technical_refs`.

| Document | Prefix | Pattern | Meaning |
|---|---|---|---|
| Implementation plan | `M` | `M1` | Workstream |
| Implementation plan | `D` | `D-01` | Plan decision |
| Implementation plan | `Q` | `Q1` | Plan question |
| Implementation plan | `G` | `G1` | Outcome target |
| Implementation plan | `DoD` | `DoD-1` | Definition-of-done item |
| Implementation plan | `P` | `P0` | Phase; derived from phase `number`, never authored as a field |
| Technical spec | `TS` | `TS-01` | Flow or sequence diagram |
| Technical spec | `C` | `C1` | Component |
| Technical spec | `CT` | `CT-01` | Contract |
| Technical spec | `PR` | `PR-01` | Processing rule |
| Technical spec | `EX` | `EX-01` | Example |
| Technical spec | `TD` | `TD-01` | Technical decision |
| Technical spec | `TQ` | `TQ1` | Technical question |

Exported answers map to the document that owns the ID.

## Business context

```json
{
  "problem": "Current workflow and quantified pain.",
  "affected": [{"group": "Ops", "impact": "2 hours/day"}],
  "why_now": "Timing trigger.",
  "glossary": [{"term": "SKU", "meaning": "One sellable variant."}]
}
```

## Goals and definition of done

```json
{
  "goal": "Ops and customers see the same stock on every channel within a minute.",
  "outcomes": [
    {"id": "G1", "goal": "Oversells", "baseline": "38/month", "target": "< 2/month", "measured_by": "Cancellation report", "check_on": "2 weeks after rollout"}
  ],
  "definition_of_done": [
    {"id": "DoD-1", "condition": "Migrations round-trip on staging (`make migrate-roundtrip`).", "verified_by": "CI job", "evidence": "CI run 412 passed", "status": "verified"},
    {"id": "DoD-2", "condition": "Ops lead signs off the rollout.", "verified_by": "Ops lead sign-off", "evidence": "", "status": "open"}
  ],
  "in_scope": ["Included outcome"],
  "out_of_scope": ["Boundary"],
  "later": ["Deferred idea"]
}
```

`goal` is one sentence: what is true, for whom, after this ships.

Every outcome needs `id`, `goal`, `baseline`, `target`, `measured_by`, and `check_on`. Outcomes are measured after delivery and never block it.

`definition_of_done` needs at least one item. Every item needs `id`, a binary `condition`, a named `verified_by`, and `status` `open` or `verified`. `evidence` is required and non-empty when status is `verified`. Every item must appear in at least one phase's `covers`.

## System shape

```json
{
  "today": ["Current step", "⚠️ Pain point"],
  "after": ["Future step", "🆕 New part"],
  "technical_spec": {"label": "Technical spec", "href": "./technical-spec.html"}
}
```

Keep both flows short and business-level. `technical_spec` is optional for plan-only output. Diagrams belong in the technical spec.

## Workstreams

Use `modules` for concise delivery slices, not technical design. Each workstream references technical-spec IDs through `technical_refs`.

```json
{
  "id": "M1",
  "title": "Stock ledger",
  "tldr": "Every stock change is recorded in one place.",
  "phase": 1,
  "status": "In progress",
  "owner": "Accountable person",
  "delivers": "Ledger and reservation API on staging",
  "depends_on": "Phase 0 findings",
  "exit_criteria": "DoD-1 verified; staging deploy",
  "technical_refs": ["CT-01", "PR-01"],
  "links": [{"label": "Board card", "href": "#"}]
}
```

IDs match `M[1-9][0-9]*`, stay unique, and never get reused. Status: `Done`, `In progress`, `Not started`, or `Blocked`. `tldr`, `owner`, `delivers`, and `exit_criteria` are required. `depends_on`, `technical_refs`, and `links` are optional. `technical_refs` accepts only technical-spec IDs from the registry. The old `fields` list is rejected.

## Decisions

```json
{
  "id": "D-01",
  "title": "Ledger is append-only",
  "tldr": "Stock is movement sum, not a mutable counter.",
  "affects": ["M1"],
  "status": "Accepted",
  "fields": [{"label": "Why", "text": "Traceability."}],
  "options": [
    {"value": "accept", "title": "Accept append-only ledger", "why": "Keeps history.", "recommended": true},
    {"value": "counter", "title": "Use mutable counter", "why": "Less code but loses history."}
  ],
  "other": true
}
```

Plan decisions cover scope, ownership, budget, schedule, rollout, hosting or procurement, and process adoption. Technical choices go to the technical spec as `TD`.

IDs match `D-[0-9]{2,}`. `affects` lists existing plan IDs (`M`, `D`, `Q`, `G`, `DoD`, `P`). Status: `Proposed`, `Accepted`, or `Superseded (by D-xx)`. `tldr` is required. Add `options` only when reviewer must choose; each choice has 2–4 options and at most one recommendation. Exactly one recommendation is required when options exist unless `recommendation_optional` is `true`. `other` defaults to `true`.

## Phases

```json
{
  "number": 0,
  "title": "Spike",
  "delivers": "Measured limits",
  "exit_criteria": "Limits documented",
  "plan": "3 d",
  "actual": "4 d",
  "status": "Done",
  "progress": 100,
  "covers": ["DoD-1"]
}
```

`covers` is required and lists the DoD IDs the phase satisfies; use `[]` when a phase satisfies none. Every ID must exist in `definition_of_done`. Phase numbers stay unique. `current_phase` must match one number. Status uses module vocabulary. `progress` is optional integer 0–100; renderer infers 100 for Done and 0 for Not started when absent.

## Risks and assumptions

```json
{
  "risks": [
    {"risk": "Rate limiting", "likelihood": "High", "impact": "High", "mitigation": "Coalesce pushes", "owner": "Owner"}
  ],
  "assumptions": [
    {"assumption": "API supports updates", "status": "Verified", "verify_by": "2026-10-10", "owner": "Owner"}
  ]
}
```

Plan risks cover adoption, staffing, timing, dependencies, approvals, and operational readiness. Technical failure modes go to the technical spec. Every risk needs mitigation and owner.

Every assumption needs `status`, `verify_by`, and `owner`. Status: `Unverified`, `Verified`, or `False`. `verify_by` is a `YYYY-MM-DD` date or a named gate. An `Unverified` assumption whose date is before `updated` fails the build: verify it or move it to the risk table.

## Rollout and rollback

```json
{
  "steps": [
    {"label": "Seed", "text": "Import and diff."},
    {"label": "Rollback", "text": "Disable channel flag; preserve ledger."}
  ],
  "point_of_no_return": "Ops retires spreadsheet after sign-off."
}
```

## Outcome metrics and observability

```json
{
  "metrics": [
    {"metric": "sync_lag_seconds", "tracks_goal": ["G2"], "alert_when": "p95 > 120 s for 10 min"}
  ]
}
```

Only metrics that track an outcome target. `tracks_goal` lists existing `G` IDs. Delivery checks belong in `definition_of_done`; technical tests and metrics belong in the technical spec. The old `verification` key is rejected.

## Open questions

```json
{
  "id": "Q1",
  "question": "Does sandbox send webhooks?",
  "owner": "Owner",
  "due": "2026-10-24",
  "blocks": "D-03",
  "evidence": [
    {"label": "Spike finding", "text": "Sandbox behavior remains unverified.", "source": "docs/spike.md:42"}
  ],
  "options": [
    {"value": "test", "title": "Test before phase 2", "why": "Closes risk before adapter work.", "recommended": true},
    {"value": "poll", "title": "Assume polling only", "why": "Starts now but spends rate budget."}
  ],
  "other": true
}
```

Technical questions live in the technical spec as `TQ`.

IDs match `Q[1-9][0-9]*`. Owner and due date are required. Every question needs `options`: 2–4 choices and exactly one recommendation unless `recommendation_optional` is true. `other` defaults to `true`, so reviewers can still type an answer the options miss. Builder rejects questions without options.

Evidence accepts `label`, `text`, `note`, `code`, and `source`, matching decision-sheet semantics.

## Change log

```json
{"version": "0.3", "date": "2026-10-19", "change": "Closed phase 0; updated estimate."}
```

At least one entry required. Every scope, decision, estimate, exit-criteria, or definition-of-done change gets an entry.

## Build

```sh
# <skill-dir> = directory containing the implementation-review SKILL.md
python3 <skill-dir>/scripts/build.py implementation-plan.json implementation-plan.html
```

Builder fails on schema/status/ID errors, unregistered ID prefixes, unknown referenced IDs, DoD items with no verifier or no covering phase, verified DoD items without evidence, `shipped`/`done` plans with open DoD items, overdue unverified assumptions, removed keys (`goals`, `diagram`, `fields`, `verification`), unsafe links, mismatched current phase, duplicate IDs, or bad recommendations. Output contains inline CSS and JavaScript only and opens from `file://`.
