---
title: <Feature> Technical Specification
doc_type: technical-spec
status: draft
version: 0.1
updated: YYYY-MM-DD
owner: <Owner>
reviewers: [<Reviewer>]
links:
  implementation plan: "./implementation-plan.html"
---

# <Feature> Technical Specification

<One-line technical outcome.>

## 1. Overview

**TL;DR:** <Purpose, main boundary, main invariant.>

- **Purpose:** <Technical outcome>
- **Context:** <Existing system and constraints>
- **Boundaries:** <Included/excluded details>
- **Principles:** <Rules shaping implementation>

## 2. Flows and sequences

### TS-01. Business process

**TL;DR:** <Actor handoffs and outcomes.>

### TS-02. Runtime sequence

**TL;DR:** <Ordering of calls and durable side effects.>

### TS-03. Processing pipeline

**TL;DR:** <Stages and failure routes.>

## 3. Architecture

**TL;DR:** <Components, ports, and dependency direction.>

### Components

| ID | Component | Responsibility | Dependencies |
|---|---|---|---|
| C1 | <Name> | <Owns> | <Ports only> |

### Ports

| Port | Direction | Operations | Adapter |
|---|---|---|---|
| <Port> | in/out | <Methods> | <Implementation> |

## 4. Contracts

### CT-01. <Webhook/API/message contract>

**TL;DR:** <Trust boundary and behavior.>

- Inputs and authority
- Outputs
- Errors
- Synthetic example

## 5. Data model

**TL;DR:** <Entity ownership and core invariant.>

- Entities and keys
- Relationships/cardinalities
- Invariants
- Logical versus physical storage note

## 6. Processing rules

### PR-01. <Rule>

**TL;DR:** <Deterministic choice.>

- Inputs
- Ordered steps
- Output
- Failure behavior
- Tests

## 7. Examples

### EX-01. <Normalization example>

**TL;DR:** <Field derivation proven by example.>

Use synthetic/redacted inputs. Show output field, value, and authority.

## 8. Reliability and failure handling

**TL;DR:** <Retry/idempotency/recovery guarantee.>

- Failure modes
- Concurrency
- Recovery
- Capacity limits and upgrade triggers

## 9. Security and privacy

**TL;DR:** <Main trust and data boundary.>

- Trust boundaries
- Sensitive data and retention
- Secret handling
- Abuse cases

## 10. Technical verification and observability

- Tests by layer
- Fixtures
- Metrics and alerts
- Release gates

## 11. Technical decisions

### TD-01. <Decision>

**TL;DR:** <Choice.>
**Status:** Proposed

- Why
- Cost
- Revisit trigger

## 12. Open technical questions

| ID | Question | Owner | Due | Blocks |
|---|---|---|---|---|
| TQ1 | <Question> | <Owner> | <Date/gate> | <Contract/rule> |

## 13. Change log

| Version | Date | Change |
|---|---|---|
| 0.1 | <Date> | First draft. |
