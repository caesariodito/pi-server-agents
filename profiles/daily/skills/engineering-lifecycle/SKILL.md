---
name: engineering-lifecycle
description: "Run consequential engineering changes through planning, canonical spec.md, dry-run review, feedback, implementation, review, fixes, and re-review. Use before consequential contract, persistent-data, architecture, security-boundary, concurrency, or recovery changes. Duration or dependent steps alone need task tracking, not documents. Small low-risk edits stay direct."
---

# Engineering lifecycle

Work directly in the current session. Separate sequential passes share context; never describe them as independent review. Herdr delegation requires an explicit request and the `herdr` skill; it does not replace this lifecycle.

## 1. Plan from evidence

Inspect applicable instructions, existing code, manifests, checks, CI, relevant ADRs, and supported runtime. Identify scope, dependencies, risks, and cheapest verification. Use relevant language guidance from `~/.pi/agent/daily-skills/project-init/references/`; preserve repository architecture and frontend design system.

Keep a short task list. Prefer deletion, stdlib, native platform, and installed dependencies. Skip this document workflow for small, low-risk, well-understood changes; still test and inspect their diff. Duration or dependent steps alone do not trigger document workflow; use task tracking when needed.

Complete when scope, applicable conventions, proposed sequence, and verification are known.

## 2. Write canonical spec.md

Use existing tracked specification convention; otherwise `docs/specs/<feature>/spec.md`. Update an existing matching spec instead of creating another authority. Outside a repository, ask for an output directory. Keep generated review pages and temporary evidence in ignored `.scratch/<feature>/`.

Keep only applicable sections:

- Problem, goal, scope, and explicit non-goals.
- Numbered, observable acceptance criteria and relevant failure cases.
- Current constraints and evidence: source paths, contracts, runtime, ADRs.
- Plan: smallest coherent slices and affected areas.
- Consequential decisions: constraint/evidence, simplest viable choice, meaningful alternative, accepted trade-off, failure outcome, and revisit trigger.
- Contracts, data invariants, trust boundaries, concurrency/recovery, rollout/rollback only where affected.
- Verification commands mapped to acceptance criteria; frontend accessibility and design-system checks when applicable.
- Open questions, review feedback/disposition, approval, current stage, and evidence of completion.

Mark assumptions. Reuse established test boundaries without asking; escalate new boundaries only when consequential. No story-count targets, speculative infrastructure, or ADR ceremony for routine choices.

Optional: load `implementation-review` or `technical-spec` only when HTML review is requested or clearly useful for a complex human review. Those structured views derive from this spec; feedback updates this file first. For browser reading of Markdown, use the shared local preview engine documented in `~/.pi/agent/daily-skills/implementation-review/SKILL.md` → Markdown preview. Render on request, not into a separate HTML copy; preserve canonical source and serve only a dedicated non-sensitive review directory.

For detailed flows, sequence, ERD, UML-style structure/state, or deployment topology, `technical-spec` may add derived `diagrams.md` rendered through local preview. Generate only relevant views; link spec IDs and assumptions, preserve canonical spec authority, and refresh diagrams after feedback. No separate approval or diagram schema.

Complete when every requirement has acceptance criteria and planned verification, and unresolved implementation blockers are explicit.

## 3. Dry-run review before implementation

Review the proposed change against actual code and configuration without applying implementation changes or mutating external systems. Trace happy paths and failures; check compatibility, data integrity, security, accessibility, design-system reuse, dependencies, rollback, and test feasibility. Check whether deletion or a smaller change meets the goal.

Record actionable findings and supporting paths in `spec.md`. A dry-run is code-grounded reasoning plus safe inspections, not a claim that unrun tests passed. Run safe validation only when useful.

Complete when proposed slices are feasible and every blocking finding is resolved or presented for user decision.

## 4. Apply feedback and approve

Present a concise spec path, decisions, dry-run findings, and remaining blockers. Obtain explicit approval of the spec before implementing complex work. A request to audit, plan, or write a spec is not implementation approval.

Apply feedback to `spec.md` first. Material scope, contract, risk, or design changes return to dry-run review and renewed approval. Reuse settled decisions; do not repeat the interview. Record approval with the scope it covers.

Complete when the current spec is approved and no implementation-blocking questions remain.

## 5. Implement approved slices

Capture baseline Git status and pre-existing edits. Make the smallest coherent diff; retain one writer per checkout. Use established tests/tooling and focused regression checks. No new dependencies without approval. Do not commit, publish, merge, or deploy without authority.

If evidence invalidates the approved design, stop affected work, update the spec, and return to review/approval. Ordinary local corrections within approved scope need no new ceremony.

Complete when all approved slices exist and focused checks pass; missing broader checks remain open.

## 6. Review actual work

Review committed changes against the recorded baseline and include staged, unstaged, and relevant untracked changes. Use two separate sequential passes in the current session:

- **Standards:** inspect correctness, security, accessibility, language/runtime and architecture conventions, error/resource handling, compatibility, and simplicity against repository rules and configured checks. Prefer local fixes or deletion; abstraction requires demonstrated benefit. A heuristic smell alone is not a defect.
- **Spec:** map every acceptance criterion to changed behavior and verification; find missing requirements, incorrect failure paths, unintended behavior, and scope creep. Canonical `spec.md` takes precedence over tickets or review views.

Verify each finding against actual source; record severity, path/line, concrete impact, evidence, and smallest correction. Keep findings from both passes distinct. For tests, exercise observable behavior through established boundaries, use independent expected results, and add a focused regression check for non-trivial logic. When using test-first work, prove the relevant test fails before fixing it. For interface changes, preserve repository vocabulary, compare the simplest viable alternative, and introduce seams only for demonstrated variation or complexity. No external skill pack is required.

Record findings and disposition in the spec. Skipped checks and pre-existing failures remain visible.

Complete when the full intended diff and each acceptance criterion have been reviewed.

## 7. Fix and re-review

Fix actionable findings within approved scope, run focused checks, then review the changed areas and their interactions again. Run required broader checks before completion. Repeat until no blocking findings remain; document justified nonblocking deferrals.

If the same blocker survives two fix rounds, stop and report evidence plus next decision instead of looping indefinitely. Scope/design changes return to the spec and approval gate. This stop condition never permits marking partial work done.

Complete when fixes pass checks and re-review finds no unresolved blocking issue.

## 8. Done with evidence

Update `spec.md` with final stage, acceptance evidence, commands/results, review disposition, and residual risks. Mark done only when all acceptance criteria are verified, required checks passed, and blocking findings are resolved. If verification is unavailable or required checks fail, leave blocked/in progress and say what is missing.

Report changed paths and verification concisely. Later business-outcome measurements do not block delivery unless explicitly part of acceptance. Preserve optional view status semantics; workflow done is not proof that later outcomes were measured.
