# technical-spec.json schema

One JSON object renders one self-contained technical specification. Prose is escaped; backticks render code and `**text**` renders bold. URLs allow relative paths, `#`, `http:`, `https:`, and `file:`.

## ID registry

Prefixes for both documents live in the [implementation-review ID registry](../../implementation-review/reference/schema.md#id-registry); that table is the single source. Technical-spec rows:

| Prefix | Pattern | Meaning | Field |
|---|---|---|---|
| `TS` | `TS-01` | Flow or sequence diagram | `flows[].id` |
| `C` | `C1` | Component | `architecture.components[].id` |
| `CT` | `CT-01` | Contract | `contracts[].id` |
| `PR` | `PR-01` | Processing rule | `processing_rules[].id` |
| `EX` | `EX-01` | Example | `examples[].id` |
| `TD` | `TD-01` | Technical decision | `decisions[].id` |
| `TQ` | `TQ1` | Technical question | `open_questions[].id` |

IDs are unique across the page. Each rendered item carries `id="<ID>"`, so other pages deep-link `./technical-spec.html#CT-01`. Plan IDs (`M`, `D-NN`, `Q`, `G`, `DoD-n`, `P`) belong to the implementation plan; reference them only in prose or `affects`.

## Top level

Required:

| Field | Shape |
|---|---|
| `title` | string |
| `doc_type` | exactly `technical-spec` |
| `status` | `draft`, `in-review`, `active`, or `done` |
| `version` | string/number |
| `updated` | `YYYY-MM-DD` |
| `owner` | string |
| `reviewers` | string[] |
| `links` | object; include `implementation plan` |
| `tagline` | string |
| `overview` | object |
| `flows` | diagram[] |
| `architecture` | object |
| `contracts` | contract[] |
| `data_model` | object |
| `processing_rules` | rule[] |
| `examples` | example[] |
| `reliability` | object |
| `security_privacy` | object |
| `verification` | object |
| `decisions` | decision[] |
| `open_questions` | question[] |
| `change_log` | change[] |

Optional: `key`, `answers_filename`, `lang`, `guides`.

Optional keys inside existing `links`: `diagram reference` links to live-rendered `./diagrams.md` and appears under sidebar Links. `flow diagrams`, `architecture diagrams`, and `data diagrams` add section-specific links, optionally with descriptive heading fragments. These do not introduce a new diagram schema or contract-ID prefixes; Mermaid lives in Markdown source.

## Overview

```json
{
  "purpose": "Technical outcome.",
  "context": "Current technical constraint.",
  "boundaries": ["In", "Excludes out"],
  "principles": ["Raw-log before parse"]
}
```

Prefix a boundary with `Excludes ` to list it under Excluded; all other boundaries render as Included. An empty side shows "None stated".

## Typed diagrams

Every diagram needs `id` matching `TS-[0-9]{2,}`, `kind`, `title`, and `tldr`.

### Flowchart

```json
{"id":"TS-01","kind":"flowchart","title":"Business flow","tldr":"One line.","steps":[{"actor":"CR","action":"Post form","outcome":"ID or error"}]}
```

### Sequence

```json
{"id":"TS-02","kind":"sequence","title":"Runtime sequence","tldr":"One line.","participants":["GOWA","Bot"],"messages":[{"from":"GOWA","to":"Bot","label":"Webhook","note":"Optional"}]}
```

### Data flow

```json
{"id":"TS-03","kind":"data-flow","title":"Pipeline","tldr":"One line.","stages":[{"name":"Verify","input":"Webhook","process":"Signature","output":"Trusted event","on_error":"Reject"}]}
```

Sequence endpoints must be declared participants. Every stage requires `name`, `input`, `process`, and `output`.

## Architecture

```json
{
  "tldr": "Three ports isolate GOWA and Sheets.",
  "components": [
    {"id":"C1","name":"Core","responsibility":"Parse and match","depends_on":["MessageSource","Store"]}
  ],
  "ports": [
    {"name":"Store","direction":"out","operations":["AppendRaw", "SaveDoneVersion"],"implemented_by":"Sheets adapter"}
  ],
  "constraints": ["One serialized writer"]
}
```

Component IDs match `C[1-9][0-9]*` and are unique. Port direction: `in` or `out`.

## Contracts

```json
{
  "id":"CT-01",
  "title":"GOWA webhook",
  "tldr":"Signed events from two group JIDs only.",
  "type":"webhook",
  "source":"GOWA OpenAPI or assumption",
  "inputs":[{"field":"id","type":"text","required":true,"authority":"GOWA payload","rule":"Dedupe key"}],
  "outputs":[{"field":"status","type":"HTTP","meaning":"2xx after durable acceptance"}],
  "errors":[{"condition":"Bad signature","outcome":"401; no row"}],
  "example":"Optional escaped text"
}
```

IDs match `CT-[0-9]{2,}`. Input fields require `field`, `type`, `required`, `authority`, and `rule`. Errors require `condition` and `outcome`.

## Data model

```json
{
  "tldr":"Transport and business identity stay separate.",
  "note":"Logical model; Sheets may flatten it.",
  "entities":[
    {"name":"raw_message","fields":[{"name":"message_id","type":"text","key":"PK","nullable":false,"invariant":"Unique transport identity"}]}
  ],
  "relationships":[{"from":"raw_message","to":"shipping","label":"produces 0..1"}],
  "invariants":["Exactly one current Done version per done_id"]
}
```

Entity names are unique. Relationship endpoints must name entities. Fields require `name` and `type`; `key`, `nullable`, `invariant`, and `note` are optional.

## Processing rules

```json
{
  "id":"PR-01",
  "title":"Matching priority",
  "tldr":"Explicit ID wins; quote is fallback.",
  "inputs":["Explicit Shipping ID", "Quoted message ID"],
  "steps":["Resolve explicit ID", "Resolve quote if explicit absent"],
  "output":"Linked Shipping or NEED REVIEW",
  "failure":"Conflicting links become NEED REVIEW",
  "tests":["Explicit and quote conflict"]
}
```

IDs match `PR-[0-9]{2,}`.

## Examples

```json
{
  "id":"EX-01",
  "title":"Shipping normalization",
  "tldr":"Shows authority for each field.",
  "input":"Synthetic form text",
  "columns":["Field","Value","Authority"],
  "rows":[["shipping_id","SHP-W000001","Persisted counter"]],
  "notes":["No personal data"]
}
```

IDs match `EX-[0-9]{2,}`. Rows must match column count.

## Reliability

```json
{
  "tldr":"Retries remain idempotent.",
  "failure_modes":[{"failure":"Quota error","detection":"API response","response":"Retry","data_safety":"No counter reuse"}],
  "concurrency":["Single writer"],
  "recovery":["Restart from persisted counter"],
  "limits":[{"limit":"Sheets write quota","ceiling":"Measured threshold","upgrade_trigger":"Sustained errors"}]
}
```

## Security and privacy

```json
{
  "tldr":"Raw messages are sensitive.",
  "trust_boundaries":[{"boundary":"GOWA webhook","control":"Signature + allowlist"}],
  "sensitive_data":[{"data":"Address","location":"RAW MESSAGES","retention":"90 days proposed","access":"Dito + DBO lead"}],
  "secrets":["Webhook secret via runtime environment"],
  "abuse_cases":[{"case":"Forged webhook","mitigation":"Reject signature"}]
}
```

## Verification

```json
{
  "tests":[{"layer":"Parser","scenario":"Unknown alias","expected":"NEED REVIEW"}],
  "metrics":[{"metric":"sheet_write_failures_total","meaning":"Store reliability","alert":"Any unrecovered failure"}],
  "fixtures":["30–50 redacted samples"],
  "gates":["Zero silent wrong links"]
}
```

## Decisions

```json
{
  "id":"TD-01",
  "title":"Serialized Sheets writer",
  "tldr":"One writer orders counters and rows.",
  "status":"Proposed",
  "affects":["C1","CT-02"],
  "fields":[{"label":"Why","text":"Sheets appends are not atomic."}],
  "options":[
    {"value":"serialized","title":"Serialize writes","why":"Avoid races.","recommended":true},
    {"value":"parallel","title":"Write concurrently","why":"Less code; race risk."}
  ]
}
```

IDs match `TD-[0-9]{2,}`. Status: `Proposed`, `Accepted`, or `Superseded (by TD-xx)`. Options: 2–4, exactly one recommended unless `recommendation_optional` is true. `other` defaults true.

## Open technical questions

```json
{
  "id":"TQ1",
  "question":"Does edited payload retain original message ID?",
  "owner":"Dito",
  "due":"Before adapter coding",
  "blocks":"CT-01",
  "evidence":[{"label":"Gap","text":"Not verified."}],
  "options":[
    {"value":"verify","title":"Capture fixture first","why":"Prevents wrong version identity.","recommended":true},
    {"value":"assume","title":"Assume shape","why":"Faster; rewrite risk."}
  ]
}
```

IDs match `TQ[1-9][0-9]*`.

## Build

```sh
# <skill-dir> = directory containing the technical-spec SKILL.md
python3 <skill-dir>/scripts/build.py technical-spec.json technical-spec.html
```
