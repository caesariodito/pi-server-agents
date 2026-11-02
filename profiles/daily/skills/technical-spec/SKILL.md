---
name: technical-spec
description: "Build optional self-contained HTML technical review views from canonical spec.md for complex human reviews or explicit HTML requests. Cover affected contracts, architecture, data, processing, failures, security, and verification separately from delivery-plan HTML."
---

# Technical spec

Turn canonical `spec.md` and repository evidence into a derived technical review page. Load `engineering-lifecycle` for canonical spec location and approval/review gates. The spec remains authoritative; JSON is renderer input and HTML is a review view. Include the canonical spec path in page links. Keep delivery sequencing and rollout ownership in `implementation-review`; link detail rather than duplicating it.

## Markdown preview and paired navigation

Follow `../implementation-review/SKILL.md` → **Markdown preview** for the shared local engine and security/snapshot rules. Render Markdown on request; never persist a separately authored Markdown-to-HTML copy. Keep interactive JSON-driven technical review and answer export intact. Both pages must list the other page and all document references under sidebar **Links**. Do not duplicate document navigation in headers. Keep contextual section deep-links.

```sh
node ~/.pi/agent/daily-skills/implementation-review/scripts/preview.mjs /absolute/path/to/review-directory
```

Refresh `.md` preview after edits. Export browser answers before changing origin; stop server with Ctrl+C.

## Detailed diagram reference

When relationships, branching, concurrency, data, or topology need more detail than the concise template provides, author optional `diagrams.md` beside review views. Render it with the shared local preview engine; no new JSON schema or Markdown-derived HTML file. Keep simple summaries in this page; link details rather than duplicating them. Do not require a third page or every diagram type for routine work.

Use fenced `mermaid` blocks for relevant types: `flowchart` for paths/architecture, `sequenceDiagram` for ordering and concurrency, `erDiagram` for keys/cardinality, `classDiagram` or `stateDiagram-v2` for UML-style structure/lifecycle. Deployment-style topology uses labeled flowchart subgraphs; do not claim full UML deployment support. Never invent classes, services, or infrastructure to fill a diagram.

Start reference with canonical spec path/version, links back to both reviews, and evidence/assumption status. Each diagram needs a stable descriptive Markdown heading, question answered, related spec/plan IDs, assumptions, and short explanation. Derived diagram anchors are heading slugs, not new contract-ID prefixes. Feedback updates spec first, then diagrams; no separate approvals or answer store.

Add `links["diagram reference"] = "./diagrams.md"` to both JSON views under sidebar Links. Optional technical-section links use existing `links` keys: `flow diagrams`, `architecture diagrams`, `data diagrams`, with heading fragments such as `./diagrams.md#entity-relationships`. Keep bidirectional links and verify every anchor.

Engine uses locally pinned Mermaid, never CDN. Setup when missing: `npm ci --ignore-scripts --prefix ~/.pi/agent/daily-skills/technical-spec`. `package.json` and lockfile pin dependency; do not update/install another dependency without approval. Strict rendering, no HTML labels/click actions/config directives. Render errors or missing engine leave visible warning and source fallback; ordinary Markdown works. Detailed diagrams require localhost preview; `file://` reviews still work but `.md` opens as source.

## Steps

1. Inspect project instructions, relevant code, API/schema docs, runtime config, deployment files, tests, and linked implementation plan. Mark unsupported claims as assumptions.
2. Read [`reference/schema.md`](reference/schema.md) and [`reference/template.md`](reference/template.md). Preserve fixed section order.
3. Resolve only blocking ambiguities or consequential choices. Use structured questions for one or two choices; put three or more genuine technical choices in the requested page.
4. Ensure `.scratch/` is ignored when working inside a repository. Write `.scratch/<feature>/technical-spec.json` and preserve stable IDs.
5. Build:
   ```sh
   # <skill-dir> = directory containing the technical-spec SKILL.md
   python3 <skill-dir>/scripts/build.py \
     .scratch/<feature>/technical-spec.json \
     .scratch/<feature>/technical-spec.html
   ```
6. Validate page opens from `file://`, contains no external assets or secrets, and links back to implementation plan.
7. Follow implementation-review browser handoff: start or reuse a verified scoped preview service and give clickable localhost links, including rendered diagrams and canonical spec, not just file paths. Reviewer can accept recommendations, change exceptions, then paste or download exported answers.
8. When answers return, handle `OTHER` first. Update canonical `spec.md`, then synchronize view JSON by stable ID, supersede changed decisions, update examples/contracts, bump version, log, and rebuild. Material changes return to lifecycle dry-run review and approval.

## Ownership boundary

Technical spec owns:

- business-to-system flow and runtime sequence;
- component boundaries and ports;
- API, webhook, command, and message contracts;
- logical/physical data model and invariants;
- parsing, normalization, matching, versioning, and processing rules;
- synthetic/redacted example input and output;
- failure handling, retries, idempotency, concurrency, and recovery;
- security, privacy, access, retention, and trust boundaries;
- technical tests, observability, capacity ceilings, and upgrade triggers;
- deep technical decisions and unresolved technical questions.

Implementation plan owns:

- business context, goals, scope, and non-goals;
- module/workstream summaries, phases, estimates, owners, and dependencies;
- rollout and rollback sequencing;
- plan-level risks, approvals, and business questions.

Link across pages by stable IDs instead of duplicating detail. Implementation plan can say `M2 implements TS-04` and deep-link `./technical-spec.html#CT-01`; technical spec can say `TD-03 affects plan M2`. Plan decisions use `D-xx`; technical decisions use `TD-xx`. Plan definition-of-done items reference "technical release gates in §10" (`verification.gates`) as one item instead of copying each gate.

The ID registry in [`../implementation-review/reference/schema.md`](../implementation-review/reference/schema.md#id-registry) is the single source for every prefix in both documents. Do not invent prefixes.

## Authoring contract

- Preserve fixed order: overview; flows and sequences; architecture; contracts; data model; processing rules; examples; reliability and failure handling; security and privacy; technical verification and observability; technical decisions; open technical questions; change log.
- Give every section and decision a one-line TL;DR.
- Keep IDs stable: flows and sequences `TS-01…`, components `C1…`, contracts `CT-01…`, processing rules `PR-01…`, examples `EX-01…`, decisions `TD-01…`, questions `TQ1…`. Each rendered item gets an anchor equal to its ID.
- Prefer typed diagrams and tables over prose walls. Keep examples synthetic or redacted.
- State authority for every derived field: payload, sender roster, parser rule, counter, or user entry.
- Define failure outcome beside happy path. Ambiguity must become explicit error or review state.
- Preserve superseded decisions as `Superseded (by TD-xx)`.
- Add 2–4 browser choices only for genuine technical decisions, with exactly one useful recommendation.
- Link large generated schemas or full OpenAPI files; embed only review-critical excerpts.
- Record contract, model, algorithm, capacity, security, or verification changes in change log.

## Completion

Done when:

- JSON validates and all sections render in fixed order;
- Implementation review sidebar link works, paired plan sidebar names Technical specification, and every ID resolves as `technical-spec.html#<ID>`;
- actor handoffs, runtime ordering, data ownership, contracts, processing rules, and failure paths are explicit;
- examples prove field derivation without personal data;
- invariants have runnable or planned checks;
- security and retention boundaries are explicit;
- review HTML is self-contained and secret-free; optional diagram page uses local pinned assets, readable source/error fallback, and no CDN;
- relevant detailed diagrams have source-version/evidence labels, correct relationships, and working sidebar/section deep-links; Mermaid syntax/render checks pass, or unavailable checks are explicitly reported;
- answer export updates technical decisions by stable ID.
