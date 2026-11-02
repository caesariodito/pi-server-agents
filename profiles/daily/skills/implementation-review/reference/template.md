---
title: <Plan title>
doc_type: implementation-plan
status: draft                  # draft | in-review | active | shipped | done | dropped
version: 0.1
updated: YYYY-MM-DD
owner: <Owner>
reviewers: [<Reviewer>]
links:
  prd: "#"
  board: "#"
  repo: "#"
  technical spec: "./technical-spec.html"
current_phase: 0
---

<!--
AUTHORING CONTRACT

1. Keep section order fixed. Delete optional content, never reorder sections.
2. Write for a technical reviewer needing business context. Technical detail lives in the technical spec.
3. Give every workstream and decision a one-line TL;DR.
4. Keep schemas, API contracts, and task lists in linked detail docs.
5. Use only IDs from the schema ID registry. Keep them stable and never reuse them: M1, D-01, Q1, G1, DoD-1.
6. Use exact status words:
   - Plan: draft | in-review | active | shipped | done | dropped
     - shipped: every DoD item is verified.
     - done: outcome targets were checked, either met or explicitly accepted as missed.
   - Phases/workstreams: Done | In progress | Not started | Blocked
   - Decisions: Proposed | Accepted | Superseded (by D-xx)
   - DoD items: open | verified
   - Assumptions: Unverified | Verified | False
7. Preserve decisions. Supersede them and link replacement.
8. Log every scope, decision, estimate, exit-criteria, or DoD change.
9. Guide text belongs in source only; final HTML hides it by default.
-->

# <Plan title>

<One-line outcome.>

## The 30-second read

| | |
|---|---|
| **Building** | <What changes.> |
| **So that** | <Measured business reason.> |
| **Done when** | <DoD and outcome IDs, e.g. "DoD-1 to DoD-5; G1 checked 2 weeks after rollout."> |
| **Biggest risk** | <Risk and mitigation or decision ID.> |
| **Now** | <Current phase and schedule state.> |

**Progress:** <One short clause per phase.> DoD verified <x> of <y>.

---

## 1. Business context

### The problem

<Current workflow, pain, and cost of doing nothing.>

### Who is affected

- **<Group>:** <Quantified impact.>

### Why now

<Timing trigger.>

### Glossary

| Term | Meaning |
|---|---|
| <Term> | <Project-specific meaning.> |

---

## 2. Goals and definition of done

**Goal:** <One sentence: what is true, for whom, after this ships.>

### Outcome targets

| ID | Goal | Baseline | Target | Measured by | Check on |
|---|---|---|---|---|---|
| G1 | <Outcome> | <Current> | <Target> | <Metric/source> | <Date or "2 weeks after rollout"> |

### Definition of done

Delivery is done when every item is verified. Outcome targets are checked later and don't block delivery.

| ID | Condition | Verified by | Evidence |
|---|---|---|---|
| DoD-1 | <Binary, checkable condition> | <Command, reviewer, or sign-off> | <Link or output; empty until verified> |

<!--
Each DoD item is binary, names a verifier, and records evidence once verified.
- Bad: "Bot handles forms correctly."
- Good: "Replaying 50 historical messages produces 0 unmatched rows (`go test ./replay -run Historical`)."
A typical set has 4 to 6 items: functional acceptance; "technical release gates in technical-spec §10 pass" as one item rather than copied tests; rollout complete per Section 8; runbook handed over; owner sign-off.
-->

### In scope

- <Included outcome>

### Out of scope

- <Explicit boundary>

### Later

- <Deferred idea>

---

## 3. System shape

### Today

1. <Current business flow; mark pain points.>

### After

1. <Future business flow; mark new parts.>

Technical detail: [Technical spec](./technical-spec.html)

---

## 4. Workstreams

### M1. <Workstream>

**TL;DR:** <One-line delivery outcome.>
**Phase:** <number> | **Status:** Not started

- **Owner:** <Accountable person>
- **Delivers:** <Observable output>
- **Depends on:** <People, approvals, or previous work>
- **Exit criteria:** <Checkable completion condition>
- **Technical detail:** <CT/PR/TD IDs in technical-spec.html>

---

## 5. Key decisions

<!--
Plan decisions cover scope, ownership, budget, schedule, rollout, hosting or procurement, and process adoption.
Technical choices go to the technical spec as TD.
-->

### D-01. <Decision>

**TL;DR:** <Choice in one line.>
**Affects:** <M1> | **Status:** Proposed

- **Why:** <Evidence-backed reason>
- **Rejected:**
  - <Option>: <Consequence>
- **Cost:** <Accepted downside>
- **Revisit if:** <Observable trigger>

---

## 6. Phases

| Phase | Delivers | Exit criteria | Covers | Plan | Actual | Status |
|---|---|---|---|---|---|---|
| ▶ 0. <Phase> | <Output> | <Externally checkable criteria> | <DoD-1, DoD-2> | <Estimate> | | Not started |

---

## 7. Risks and assumptions

<!--
Plan risks cover adoption, staffing, timing, dependencies, approvals, and operational readiness.
Technical failure modes go to the technical spec.
-->

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| <Delivery risk> | <Low/Medium/High> | <Low/Medium/High> | <Concrete response> | <Owner> |

### Assumptions

| Assumption | Status | Verify by | Owner |
|---|---|---|---|
| <Belief> | Unverified | <YYYY-MM-DD or gate> | <Owner> |

An unverified assumption past its "Verify by" date moves to the risk table.

---

## 8. Rollout and rollback

- **Rollout:** <Safe sequence>
- **Flags:** <Kill switches or staged controls>
- **Rollback:** <Code and data behavior>

> **Point of no return:** <Irreversible transition and approval gate.>

---

## 9. Outcome metrics and observability

| Metric | Tracks goal | Alert when |
|---|---|---|
| `<metric>` | <G1> | <Threshold and window> |

---

## 10. Open questions

Technical questions live in the technical spec as TQ. Every question offers 2–4 answer choices with one recommended; reviewers answer in the browser.

| # | Question | Owner | Due | Blocks |
|---|---|---|---|---|
| Q1 | <Answerable question> | <Owner> | <Date> | <D-xx/Mx/DoD-x/phase> |

---

## 11. Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | <Date> | First draft. |
