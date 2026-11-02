from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

OTHER = "__other"
INLINE = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<b>\1</b>"),
)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def inline(value: object) -> str:
    out = esc(value)
    for pattern, replacement in INLINE:
        out = pattern.sub(replacement, out)
    return out


def slug(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def safe_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def safe_url(value: object) -> str:
    text = str(value)
    parsed = urlsplit(text)
    if parsed.scheme.lower() not in {"", "http", "https", "file"} or text.startswith("//"):
        raise ValueError(f"unsafe URL {text!r}")
    return text


def link(label: object, href: object) -> str:
    return f'<a href="{esc(safe_url(href))}">{inline(label)}</a>'


def sentence_case(label: object) -> str:
    text = str(label)
    return text[:1].upper() + text[1:]


def tag(value: object) -> str:
    css = {
        "draft": "draft",
        "in-review": "proposed",
        "active": "decided",
        "done": "decided",
        "Proposed": "proposed",
        "Accepted": "decided",
    }.get(str(value), "open")
    return f'<span class="tag {css}">{inline(value)}</span>'


def table(headers: list[str], rows: list[list[str]], row_ids: list[str] | None = None) -> str:
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    ids = row_ids or [""] * len(rows)
    body = "".join((f'<tr id="{esc(row_id)}">' if row_id else "<tr>") + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row, row_id in zip(rows, ids))
    if not body:
        body = f'<tr><td colspan="{len(headers)}">None.</td></tr>'
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def guide(spec: dict, key: str, default: str) -> str:
    text = spec.get("guides", {}).get(key, default)
    return f'<aside class="guide"><strong>Writing guide.</strong> {inline(text)}</aside>'


def section(spec: dict, number: str, title: str, anchor: str, key: str, default_guide: str, lede: str = "") -> str:
    lede_html = f'<p class="lede">{inline(lede)}</p>' if lede else ""
    return (
        f'<section class="sec" id="{anchor}" aria-labelledby="h-{anchor}">'
        f'<h2 id="h-{anchor}"><span class="num">{number}</span>{inline(title)}</h2>'
        f'{lede_html}{guide(spec, key, default_guide)}'
    )


def item_head(item_id: str, title: str, badge: str = "") -> str:
    badge_html = f'<span class="tag">{inline(badge)}</span>' if badge else ""
    return (
        f'<div class="item-head"><button class="item-id" data-anchor="{esc(item_id)}" title="Copy link">'
        f'{esc(item_id)}</button>{badge_html}<h3>{inline(title)}</h3></div>'
    )


def evidence(items: list[dict]) -> str:
    parts: list[str] = []
    for item in items:
        if item.get("label"):
            parts.append(f'<h4>{inline(item["label"])}</h4>')
        if item.get("text"):
            parts.append(f'<p>{inline(item["text"])}</p>')
        if item.get("code") is not None:
            source = f'{item.get("source")}\n' if item.get("source") else ""
            parts.append(f'<pre>{esc(source + str(item["code"]))}</pre>')
    return "".join(parts)


def choices(item: dict) -> str:
    options = item.get("options")
    if not options:
        return ""
    item_id = str(item["id"])
    rows: list[str] = []
    for option in options:
        recommended = '<span class="rec">Recommended</span>' if option.get("recommended") else ""
        rows.append(
            f'<label class="choice"><input type="radio" name="{esc(item_id)}" value="{esc(option["value"])}" '
            f'data-recommended="{str(bool(option.get("recommended"))).lower()}">'
            f'<span class="choice-title">{inline(option["title"])}{recommended}</span>'
            f'<span class="choice-desc">{inline(option.get("why", ""))}</span></label>'
        )
    if item.get("other", True):
        rows.append(
            f'<label class="choice"><input type="radio" name="{esc(item_id)}" value="{OTHER}" data-recommended="false">'
            '<span class="choice-title">Something else</span>'
            '<span class="choice-desc">Reject listed choices and type replacement.</span></label>'
            f'<textarea data-other="{esc(item_id)}" hidden placeholder="Replacement decision"></textarea>'
        )
    return (
        '<div class="answer"><h4>Your answer</h4><fieldset class="choices"><legend>Choose one</legend>'
        + "".join(rows)
        + '</fieldset><label class="free">Comment <span class="no">optional</span></label>'
        '<textarea class="review-comment" placeholder="Why, exception, or constraint"></textarea></div>'
    )


def flow_figure(diagram: dict) -> str:
    if diagram["kind"] == "flowchart":
        nodes = []
        for index, step in enumerate(diagram["steps"], 1):
            outcome = f'<span class="native-outcome">{inline(step["outcome"])}</span>' if step.get("outcome") else ""
            nodes.append(
                f'<div class="native-node"><span class="native-index">{index}</span><span class="native-actor">{inline(step["actor"])}</span>'
                f'<strong>{inline(step["action"])}</strong>{outcome}</div>'
            )
        visual = '<ol class="native-flow">' + "".join(f"<li>{node}</li>" for node in nodes) + "</ol>"
    elif diagram["kind"] == "sequence":
        participants = "".join(f'<span>{inline(name)}</span>' for name in diagram["participants"])
        messages = "".join(
            f'<li><span class="native-index">{index}</span><div class="native-message">'
            f'<span class="native-route"><strong>{inline(message["from"])}</strong> → <strong>{inline(message["to"])}</strong></span>'
            f'<span class="native-label">{inline(message["label"])}</span>'
            f'{f"<small>{inline(message["note"])}</small>" if message.get("note") else ""}</div></li>'
            for index, message in enumerate(diagram["messages"], 1)
        )
        visual = f'<div class="native-participants">{participants}</div><ol class="native-sequence">{messages}</ol>'
    else:
        stages = []
        for index, stage in enumerate(diagram["stages"], 1):
            failure = f'<span class="native-failure">Failure: {inline(stage["on_error"])}</span>' if stage.get("on_error") else ""
            stages.append(
                f'<div class="native-stage"><span class="native-index">{index}</span><strong>{inline(stage["name"])}</strong>'
                f'<dl><dt>Input</dt><dd>{inline(stage["input"])}</dd><dt>Process</dt><dd>{inline(stage["process"])}</dd>'
                f'<dt>Output</dt><dd>{inline(stage["output"])}</dd></dl>{failure}</div>'
            )
        visual = '<ol class="native-flow">' + "".join(f"<li>{stage}</li>" for stage in stages) + "</ol>"
    return (
        f'<figure id="{esc(diagram["id"])}" data-diagram="{esc(diagram["id"])}" data-kind="{esc(diagram["kind"])}">'
        f'<div class="diagram">{visual}</div><figcaption><strong>{inline(diagram["title"])}.</strong> '
        f'{inline(diagram["tldr"])}</figcaption></figure>'
    )


def sidebar(spec: dict) -> str:
    navigation = [
        ("overview", "1", "Overview", ""), ("flows", "2", "Flows and sequences", ""),
        ("architecture", "3", "Architecture", ""), ("contracts", "4", "Contracts", ""),
        ("data-model", "5", "Data model", ""), ("rules", "6", "Processing rules", ""),
        ("examples", "7", "Examples", ""), ("reliability", "8", "Reliability", ""),
        ("security", "9", "Security and privacy", ""), ("verification", "10", "Verification", ""),
        ("decisions", "11", "Technical decisions", "decisions"),
        ("questions", "12", "Open questions", "questions"), ("changelog", "13", "Change log", ""),
        ("review", "+", "Your review", ""),
    ]
    nav_items = []
    for anchor, number, title, count in navigation:
        badge = f'<span class="count" data-count-for="{count}"></span>' if count else ""
        nav_items.append(f'<li><a href="#{anchor}"><span class="n">{number}</span>{title}{badge}</a></li>')
    links = "".join(f'<li>{link(sentence_case(label), href)}</li>' for label, href in spec["links"].items())
    reviewers = ", ".join(str(value) for value in spec["reviewers"]) or "None"
    return (
        '<aside class="sidebar" id="sidebar" aria-label="Document information and navigation">'
        f'<div class="sb-title">{inline(spec["title"])}</div>{tag(spec["status"])}'
        f'<dl class="sb-meta"><dt>Version</dt><dd>{inline(spec["version"])}</dd><dt>Updated</dt><dd>{esc(spec["updated"])}</dd>'
        f'<dt>Owner</dt><dd>{inline(spec["owner"])}</dd><dt>Reviewers</dt><dd>{inline(reviewers)}</dd></dl>'
        f'<div class="sb-block"><h2>Links</h2><ul class="sb-links">{links}</ul></div>'
        '<div class="sb-block"><h2>Review progress</h2><div class="progress" aria-hidden="true"><span id="progress-bar"></span></div>'
        '<div id="progress-label">0 of 0 answered</div></div>'
        f'<nav class="sb-block nav" aria-label="Sections"><h2>Sections</h2><ol>{"".join(nav_items)}</ol></nav></aside>'
    )


def render(spec: dict, asset_dir: Path) -> str:
    css = (asset_dir / "spec.css").read_text()
    js = (asset_dir / "spec.js").read_text()
    parts: list[str] = []
    def diagram_link(key: str) -> str:
        href = spec["links"].get(key)
        return f'<p>{link("Detailed diagram reference", href)}</p>' if href else ""

    overview = spec["overview"]
    included = [value for value in overview["boundaries"] if not str(value).lower().startswith("excludes")]
    excluded = [sentence_case(str(value)[8:].strip()) for value in overview["boundaries"] if str(value).lower().startswith("excludes")]
    def items(values: list) -> str:
        return "".join(f'<li>{inline(value)}</li>' for value in values) or '<li class="empty">None stated</li>'
    parts.append(
        section(spec, "1", "Overview", "overview", "overview", "Summarize purpose, exclusions, and tie-breaking principles in one screen.")
        + f'<h3 class="sub">Purpose</h3><p>{inline(overview["purpose"])}</p>'
        + f'<h3 class="sub">Current technical context</h3><p>{inline(overview["context"])}</p>'
        + '<h3 class="sub">Boundaries</h3><div class="split"><div class="in"><h4>Included</h4><ul>'
        + items(included)
        + '</ul></div><div class="out"><h4>Excluded</h4><ul>'
        + items(excluded)
        + '</ul></div></div><h3 class="sub">Design principles</h3><ul>'
        + "".join(f'<li>{inline(value)}</li>' for value in overview["principles"])
        + f'</ul><p>Delivery sequencing lives in {link("implementation plan", spec["links"].get("implementation plan", "#"))}.</p></section>'
    )

    parts.append(
        section(spec, "2", "Flows and sequences", "flows", "flows", "Use one visual per question: business flow, runtime order, and data transformation.")
        + "".join(flow_figure(diagram) for diagram in spec["flows"])
        + diagram_link("flow diagrams") + "</section>"
    )

    architecture = spec["architecture"]
    component_rows = [[esc(item["id"]), inline(item["name"]), inline(item["responsibility"]), inline(", ".join(item["depends_on"]))] for item in architecture["components"]]
    port_rows = [[f'<code>{inline(item["name"])}</code>', inline(item["direction"]), inline(", ".join(item["operations"])), inline(item["implemented_by"])] for item in architecture["ports"]]
    parts.append(
        section(spec, "3", "Architecture", "architecture", "architecture", "List responsibility-owning components, dependency direction, and constraints.", architecture["tldr"])
        + diagram_link("architecture diagrams")
        + f'<h3 class="sub">Components</h3>{table(["ID", "Component", "Responsibility", "Depends on"], component_rows, [str(item["id"]) for item in architecture["components"]])}'
        + f'<h3 class="sub">Ports</h3>{table(["Port", "Direction", "Operations", "Adapter"], port_rows)}'
        + '<h3 class="sub">Constraints</h3><ul>' + "".join(f'<li>{inline(value)}</li>' for value in architecture["constraints"]) + "</ul></section>"
    )

    contract_items = []
    for contract in spec["contracts"]:
        input_rows = [[f'<code>{inline(item["field"])}</code>', inline(item["type"]), '<span class="yes">Yes</span>' if item["required"] else '<span class="no">No</span>', inline(item["authority"]), inline(item["rule"])] for item in contract["inputs"]]
        output_rows = [[f'<code>{inline(item.get("field", ""))}</code>', inline(item.get("type", "")), inline(item.get("meaning", ""))] for item in contract["outputs"]]
        error_rows = [[inline(item["condition"]), inline(item["outcome"])] for item in contract["errors"]]
        example = f'<details><summary>Payload example <span class="hint">synthetic</span></summary><div class="body"><pre>{esc(contract["example"])}</pre></div></details>' if contract.get("example") else ""
        contract_items.append(
            f'<article class="item" id="{esc(contract["id"])}">{item_head(contract["id"], contract["title"], contract["type"])}'
            f'<p class="tldr">{inline(contract["tldr"])}</p><dl class="facts"><dt>Source</dt><dd>{inline(contract["source"])}</dd></dl>'
            f'<h4>Inputs</h4>{table(["Field", "Type", "Required", "Authority", "Validation"], input_rows)}'
            f'<h4>Outputs</h4>{table(["Field", "Type", "Meaning"], output_rows)}'
            f'<h4>Errors</h4>{table(["Condition", "Outcome"], error_rows)}{example}</article>'
        )
    parts.append(section(spec, "4", "Contracts", "contracts", "contracts", "One contract per boundary. Name field authority and every failure outcome.", "Everything crossing a trust boundary, and exactly what is accepted.") + "".join(contract_items) + "</section>")

    model = spec["data_model"]
    relationship_rows = [[f'<code>{inline(item["from"])}</code>', inline(item["label"]), f'<code>{inline(item["to"])}</code>'] for item in model["relationships"]]
    entity_items = []
    for entity in model["entities"]:
        rows = [[f'<code>{inline(field["name"])}</code>', inline(field["type"]), inline(field.get("key", "")), '<span class="yes">Yes</span>' if field.get("nullable") else '<span class="no">No</span>', inline(field.get("invariant", field.get("note", "")))] for field in entity["fields"]]
        entity_items.append(f'<details><summary><code>{inline(entity["name"])}</code> <span class="hint">logical entity</span></summary><div class="body">{table(["Field", "Type", "Key", "Null", "Invariant"], rows)}</div></details>')
    parts.append(
        section(spec, "5", "Data model", "data-model", "data_model", "Describe logical truth, not current sheet layout.", model["tldr"])
        + diagram_link("data diagrams")
        + f'<div class="note"><p>{inline(model.get("note", ""))}</p></div><h3 class="sub">Relationships</h3>'
        + table(["From", "Relationship", "To"], relationship_rows)
        + '<h3 class="sub">Entities</h3>' + "".join(entity_items)
        + '<h3 class="sub">Cross-entity invariants</h3><ul>' + "".join(f'<li>{inline(value)}</li>' for value in model["invariants"]) + "</ul></section>"
    )

    rules = []
    for rule in spec["processing_rules"]:
        rules.append(
            f'<article class="item" id="{esc(rule["id"])}">{item_head(rule["id"], rule["title"])}'
            f'<p class="tldr">{inline(rule["tldr"])}</p><dl class="facts"><dt>Inputs</dt><dd>{inline(", ".join(rule["inputs"]))}</dd>'
            f'<dt>Output</dt><dd>{inline(rule["output"])}</dd></dl><h4>Algorithm</h4><ol>'
            + "".join(f'<li>{inline(value)}</li>' for value in rule["steps"])
            + f'</ol><h4>Failure behavior</h4><p>{inline(rule["failure"])}</p><h4>Required tests</h4><ul>'
            + "".join(f'<li>{inline(value)}</li>' for value in rule["tests"])
            + "</ul></article>"
        )
    parts.append(section(spec, "6", "Processing rules", "rules", "processing_rules", "Write deterministic steps, output, failure behavior, and tests.", "Deterministic behavior: same input, same output.") + "".join(rules) + "</section>")

    examples = []
    for example in spec["examples"]:
        examples.append(
            f'<article class="item" id="{esc(example["id"])}">{item_head(example["id"], example["title"], "Synthetic example")}'
            f'<p class="tldr">{inline(example["tldr"])}</p><details open><summary>Input</summary><div class="body"><pre>{esc(example["input"])}</pre></div></details>'
            f'<h4>Normalized output</h4>{table(example["columns"], [[inline(cell) for cell in row] for row in example["rows"]])}<ul>'
            + "".join(f'<li>{inline(value)}</li>' for value in example.get("notes", [])) + "</ul></article>"
        )
    parts.append(section(spec, "7", "Examples", "examples", "examples", "Use synthetic/redacted data and show authority for each output.") + "".join(examples) + "</section>")

    reliability = spec["reliability"]
    failure_rows = [[inline(item["failure"]), inline(item["detection"]), inline(item["response"]), inline(item["data_safety"])] for item in reliability["failure_modes"]]
    limit_rows = [[inline(item["limit"]), inline(item["ceiling"]), inline(item["upgrade_trigger"])] for item in reliability["limits"]]
    parts.append(
        section(spec, "8", "Reliability", "reliability", "reliability", "For each failure: detection, response, and data guarantee.", reliability["tldr"])
        + table(["Failure", "Detection", "Response", "Data guarantee"], failure_rows)
        + '<div class="split"><div><h4>Concurrency</h4><ul>' + "".join(f'<li>{inline(value)}</li>' for value in reliability["concurrency"])
        + '</ul></div><div><h4>Recovery</h4><ul>' + "".join(f'<li>{inline(value)}</li>' for value in reliability["recovery"])
        + f'</ul></div></div><h3 class="sub">Limits and upgrade triggers</h3>{table(["Limit", "Current ceiling", "Upgrade trigger"], limit_rows)}</section>'
    )

    security = spec["security_privacy"]
    trust_rows = [[inline(item["boundary"]), inline(item["control"])] for item in security["trust_boundaries"]]
    data_rows = [[inline(item["data"]), inline(item["location"]), inline(item["retention"]), inline(item["access"])] for item in security["sensitive_data"]]
    abuse_rows = [[inline(item["case"]), inline(item["mitigation"])] for item in security["abuse_cases"]]
    parts.append(
        section(spec, "9", "Security and privacy", "security", "security_privacy", "Name trust boundaries, sensitive stores, retention, access, secrets, and abuse mitigations.", security["tldr"])
        + f'<h3 class="sub">Trust boundaries</h3>{table(["Boundary", "Control"], trust_rows)}'
        + f'<h3 class="sub">Sensitive data</h3>{table(["Data", "Location", "Retention", "Access"], data_rows)}'
        + '<h3 class="sub">Secrets</h3><ul>' + "".join(f'<li>{inline(value)}</li>' for value in security["secrets"])
        + f'</ul><h3 class="sub">Abuse cases</h3>{table(["Case", "Mitigation"], abuse_rows)}</section>'
    )

    verification = spec["verification"]
    test_rows = [[inline(item["layer"]), inline(item["scenario"]), inline(item["expected"])] for item in verification["tests"]]
    metric_rows = [[f'<code>{inline(item["metric"])}</code>', inline(item["meaning"]), inline(item["alert"])] for item in verification["metrics"]]
    parts.append(
        section(spec, "10", "Verification", "verification", "verification", "Tests must be runnable, gates binary, and alerts thresholded.")
        + f'<h3 class="sub">Tests</h3>{table(["Layer", "Scenario", "Expected"], test_rows)}'
        + '<h3 class="sub">Fixtures</h3><ul>' + "".join(f'<li>{inline(value)}</li>' for value in verification["fixtures"])
        + f'</ul><h3 class="sub">Metrics and alerts</h3>{table(["Metric", "Meaning", "Alert"], metric_rows)}'
        + '<h3 class="sub">Release gates</h3><ul>' + "".join(f'<li>{inline(value)}</li>' for value in verification["gates"]) + "</ul></section>"
    )

    decisions = []
    for decision in spec["decisions"]:
        facts = "".join(f'<dt>{inline(item["label"])}</dt><dd>{inline(item["text"])}</dd>' for item in decision.get("fields", []))
        decisions.append(
            f'<article class="item" id="{esc(decision["id"])}" data-answer="{esc(decision["id"])}" data-title="{esc(decision["title"])}">'
            f'{item_head(decision["id"], decision["title"])}{tag(decision["status"])}<p class="tldr">{inline(decision["tldr"])}</p>'
            f'<dl class="facts"><dt>Affects</dt><dd>{inline(", ".join(decision["affects"]))}</dd>{facts}</dl>'
            f'{evidence(decision.get("evidence", []))}{choices(decision)}</article>'
        )
    parts.append(section(spec, "11", "Technical decisions", "decisions", "decisions", "Record choices expensive to reverse, their cost, and revisit trigger.", "Choices shaping implementation and costing more than a day to undo.") + "".join(decisions) + "</section>")

    questions = []
    for question in spec["open_questions"]:
        questions.append(
            f'<article class="item" id="{esc(question["id"])}" data-answer="{esc(question["id"])}" data-title="{esc(question["question"])}">'
            f'{item_head(question["id"], question["question"])}<span class="tag open">Open</span><p class="tldr">{inline(question["question"])}</p>'
            f'<dl class="facts"><dt>Owner</dt><dd>{inline(question["owner"])}</dd><dt>Due</dt><dd>{inline(question["due"])}</dd>'
            f'<dt>Blocks</dt><dd>{inline(question["blocks"])}</dd></dl>{evidence(question.get("evidence", []))}{choices(question)}</article>'
        )
    parts.append(section(spec, "12", "Open questions", "questions", "open_questions", "Each question needs owner, gate, evidence, and blocked contract/rule.", "Unknowns blocking a contract, rule, decision, or release gate.") + "".join(questions) + "</section>")

    change_rows = [[inline(item["version"]), inline(item["date"]), inline(item["change"]), inline(item.get("reason", ""))] for item in spec["change_log"]]
    parts.append(section(spec, "13", "Change log", "changelog", "change_log", "Log contract, model, algorithm, reliability, and security changes with reasons.") + table(["Version", "Date", "Change", "Reason"], change_rows) + "</section>")

    key = spec.get("key") or f'{slug(spec["title"])}-{spec["updated"]}-v{slug(spec["version"])}'
    filename = spec.get("answers_filename") or f'{slug(spec["title"])}-answers.md'
    return f'''<!doctype html><html lang="{esc(spec.get("lang", "en"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{esc(spec["title"])}</title><style>{css}</style></head><body data-spec-id="{esc(slug(spec["title"]))}" data-spec-version="{esc(spec["version"])}"><div class="layout">{sidebar(spec)}<div class="main"><header class="masthead"><h1>{inline(spec["title"])}</h1><p class="tagline">{inline(spec["tagline"])}</p></header><div class="toolbar" role="toolbar" aria-label="Review tools"><button class="btn btn-quiet menu-btn" id="btn-menu" aria-controls="sidebar" aria-expanded="false">Sections</button><div class="group"><button class="btn btn-primary" id="btn-accept">Accept recommendations</button><button class="btn" data-action="copy">Copy answers</button><button class="btn" data-action="download">Download answers</button></div><span class="spacer"></span><div class="group"><button class="btn btn-quiet" id="btn-guide" aria-pressed="false">Writing guide</button><button class="btn btn-quiet" id="btn-theme">Theme: Auto</button><button class="btn btn-danger" id="btn-clear">Clear answers</button></div></div><main class="doc" id="doc">{"".join(parts)}<footer class="review" id="review"><h2>Your review</h2><p>Anything this spec misses, gets wrong, or should cut.</p><label class="free" for="missed">Anything missed?</label><textarea id="missed" rows="5" placeholder="Gaps, risks, wrong assumptions"></textarea><div class="actions"><button class="btn btn-primary" data-action="copy">Copy answers</button><button class="btn" data-action="download">Download answers</button></div><details><summary>Preview export <span class="hint">Markdown, updates as you answer</span></summary><div class="body"><pre id="export"></pre></div></details></footer></main></div></div><div class="toast" id="toast" role="status" aria-live="polite"></div><script>const KEY={safe_json(key)},TITLE={safe_json(spec["title"])},VERSION={safe_json(str(spec["version"]))},FILENAME={safe_json(filename)};{js}</script></body></html>'''
