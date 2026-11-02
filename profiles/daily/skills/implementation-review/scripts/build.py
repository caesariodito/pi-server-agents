#!/usr/bin/env python3
"""Build one self-contained implementation-plan HTML page.

Usage:
    python3 build.py implementation-plan.json implementation-plan.html
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MODULE_STATUSES = {"Done", "In progress", "Not started", "Blocked"}
PLAN_STATUSES = {"draft", "in-review", "active", "shipped", "done", "dropped"}
DELIVERED_STATUSES = {"shipped", "done"}
ASSUMPTION_STATUSES = {"Verified", "Unverified", "False"}
DOD_STATUSES = {"open", "verified"}
# Stable-ID registry: prefix -> (pattern, example, owning document). Keep in sync with reference/schema.md.
PLAN_IDS = {
    "M": (r"M[1-9][0-9]*", "M1", "implementation plan"),
    "D": (r"D-[0-9]{2,}", "D-01", "implementation plan"),
    "Q": (r"Q[1-9][0-9]*", "Q1", "implementation plan"),
    "G": (r"G[1-9][0-9]*", "G1", "implementation plan"),
    "DoD": (r"DoD-[1-9][0-9]*", "DoD-1", "implementation plan"),
    "P": (r"P[0-9]+", "P0", "implementation plan"),
}
TECH_IDS = {
    "TS": (r"TS-[0-9]{2,}", "TS-01", "technical spec"),
    "C": (r"C[1-9][0-9]*", "C1", "technical spec"),
    "CT": (r"CT-[0-9]{2,}", "CT-01", "technical spec"),
    "PR": (r"PR-[0-9]{2,}", "PR-01", "technical spec"),
    "EX": (r"EX-[0-9]{2,}", "EX-01", "technical spec"),
    "TD": (r"TD-[0-9]{2,}", "TD-01", "technical spec"),
    "TQ": (r"TQ[1-9][0-9]*", "TQ1", "technical spec"),
}
ID_REGISTRY = {**PLAN_IDS, **TECH_IDS}
RENAMED = (
    ("goals_scope", "goals", "'goals' was renamed to 'outcomes'; add 'id' and 'check_on' to each"),
    ("system_shape", "diagram", "'diagram' was removed; link the technical spec with 'technical_spec'"),
)
SUMMARY_FIELDS = ("building", "so_that", "done_when", "biggest_risk", "now")
SUMMARY_LABELS = {
    "building": "Building",
    "so_that": "So that",
    "done_when": "Done when",
    "biggest_risk": "Biggest risk",
    "now": "Now",
}
INLINE = (
    (re.compile(r"`([^`]+)`"), r"<code>\1</code>"),
    (re.compile(r"\*\*([^*]+)\*\*"), r"<b>\1</b>"),
)
OTHER = "__other"


def die(message: str) -> None:
    raise ValueError(message)


def require(obj: dict, field: str, where: str) -> object:
    if field not in obj:
        die(f"{where}: missing '{field}'")
    value = obj[field]
    if value is None or value == "":
        die(f"{where}: empty '{field}'")
    return value


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


def validate_url(value: object, where: str) -> str:
    url = str(value)
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"", "http", "https", "file"}:
        die(f"{where}: unsafe URL scheme in {url!r}")
    if url.startswith("//"):
        die(f"{where}: protocol-relative URL is not allowed")
    return url


def validate_options(item: dict, where: str) -> None:
    options = item.get("options")
    if options is None:
        return
    if not isinstance(options, list) or not 2 <= len(options) <= 4:
        die(f"{where}: options must contain 2–4 choices")
    values: list[str] = []
    recommended = 0
    for index, option in enumerate(options, 1):
        require(option, "value", f"{where} option {index}")
        require(option, "title", f"{where} option {index}")
        value = str(option["value"])
        if value == OTHER:
            die(f"{where}: option value {OTHER!r} is reserved")
        values.append(value)
        recommended += bool(option.get("recommended"))
    if len(values) != len(set(values)):
        die(f"{where}: duplicate option values")
    expected = {0, 1} if item.get("recommendation_optional") else {1}
    if recommended not in expected:
        die(f"{where}: expected {'at most one' if item.get('recommendation_optional') else 'exactly one'} recommended option, got {recommended}")


def check_id(value: object, allowed: dict, where: str) -> str:
    """Fail unless value is a well-formed ID whose prefix is registered in allowed."""
    text = str(value)
    match = re.match(r"[A-Za-z]+", text)
    prefix = match.group(0) if match else ""
    if prefix not in ID_REGISTRY:
        registered = ", ".join(example for _, example, _ in ID_REGISTRY.values())
        die(f"{where}: unregistered ID prefix {prefix!r} in {text!r}; registered IDs look like {registered}")
    pattern, example, owner = ID_REGISTRY[prefix]
    if prefix not in allowed:
        expected = ", ".join(item[1] for item in allowed.values())
        die(f"{where}: {text!r} belongs to the {owner}; expected one of {expected}")
    if not re.fullmatch(pattern, text):
        die(f"{where}: invalid ID {text!r}; expected format like {example}")
    return text


def check_refs(values: object, allowed: dict, known: set[str] | None, where: str) -> None:
    if not isinstance(values, list):
        die(f"{where}: must be an array of IDs")
    for value in values:
        ref = check_id(value, allowed, where)
        if known is not None and ref not in known:
            die(f"{where}: unknown ID {ref!r}")


def validate(spec: dict) -> None:
    if "verification" in spec:
        die("plan: 'verification' was renamed to 'observability'; keep metrics there and move tests into definition_of_done")
    for section, old, message in RENAMED:
        if isinstance(spec.get(section), dict) and old in spec[section]:
            die(f"{section}: {message}")
    top = (
        "title", "doc_type", "status", "version", "updated", "owner", "reviewers", "links",
        "current_phase", "tagline", "summary", "business_context", "goals_scope", "system_shape",
        "modules", "decisions", "phases", "risks_assumptions", "rollout_rollback", "observability",
        "open_questions", "change_log",
    )
    for field in top:
        require(spec, field, "plan")
    if spec["doc_type"] != "implementation-plan":
        die("plan: doc_type must be 'implementation-plan'")
    if spec["status"] not in PLAN_STATUSES:
        die(f"plan: invalid status {spec['status']!r}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(spec["updated"])):
        die("plan: updated must use YYYY-MM-DD")
    if not isinstance(spec["reviewers"], list):
        die("plan: reviewers must be an array")
    if not isinstance(spec["links"], dict):
        die("plan: links must be an object")
    for label, url in spec["links"].items():
        validate_url(url, f"link {label!r}")

    for field in SUMMARY_FIELDS:
        require(spec["summary"], field, "summary")

    business = spec["business_context"]
    for field in ("problem", "affected", "why_now", "glossary"):
        require(business, field, "business_context")
    for index, item in enumerate(business["affected"], 1):
        require(item, "group", f"affected item {index}")
        require(item, "impact", f"affected item {index}")
    for index, item in enumerate(business["glossary"], 1):
        require(item, "term", f"glossary item {index}")
        require(item, "meaning", f"glossary item {index}")

    ids: list[str] = []
    scope = spec["goals_scope"]
    require(scope, "goal", "goals_scope")
    for field in ("outcomes", "definition_of_done", "in_scope", "out_of_scope", "later"):
        if field not in scope:
            die(f"goals_scope: missing '{field}'")
    for index, outcome in enumerate(scope["outcomes"], 1):
        outcome_id = check_id(require(outcome, "id", f"outcome {index}"), {"G": PLAN_IDS["G"]}, f"outcome {index}")
        ids.append(outcome_id)
        for field in ("goal", "baseline", "target", "measured_by", "check_on"):
            require(outcome, field, outcome_id)
    if not scope["definition_of_done"]:
        die("goals_scope: definition_of_done needs at least one item")
    dod_ids: list[str] = []
    for index, item in enumerate(scope["definition_of_done"], 1):
        dod_id = check_id(require(item, "id", f"definition_of_done item {index}"), {"DoD": PLAN_IDS["DoD"]}, f"definition_of_done item {index}")
        dod_ids.append(dod_id)
        for field in ("condition", "verified_by", "status"):
            require(item, field, dod_id)
        if item["status"] not in DOD_STATUSES:
            die(f"{dod_id}: invalid status {item['status']!r}; use 'open' or 'verified'")
        if item["status"] == "verified" and not str(item.get("evidence") or "").strip():
            die(f"{dod_id}: status 'verified' needs non-empty 'evidence'")
    ids.extend(dod_ids)
    if spec["status"] in DELIVERED_STATUSES:
        still_open = [item["id"] for item in scope["definition_of_done"] if item["status"] != "verified"]
        if still_open:
            die(f"plan: status {spec['status']!r} needs every DoD item verified; still open: {', '.join(still_open)}")

    shape = spec["system_shape"]
    for field in ("today", "after"):
        require(shape, field, "system_shape")
    if shape.get("technical_spec"):
        require(shape["technical_spec"], "label", "system_shape technical_spec")
        validate_url(require(shape["technical_spec"], "href", "system_shape technical_spec"), "system_shape technical_spec")

    for index, module in enumerate(spec["modules"], 1):
        module_id = check_id(require(module, "id", f"workstream {index}"), {"M": PLAN_IDS["M"]}, f"workstream {index}")
        ids.append(module_id)
        if "fields" in module:
            die(f"{module_id}: 'fields' was removed; use owner, delivers, depends_on, exit_criteria, and technical_refs")
        for field in ("title", "tldr", "phase", "status", "owner", "delivers", "exit_criteria"):
            require(module, field, module_id)
        if module["status"] not in MODULE_STATUSES:
            die(f"{module_id}: invalid status {module['status']!r}")
        check_refs(module.get("technical_refs", []), TECH_IDS, None, f"{module_id} technical_refs")
        for link in module.get("links", []):
            require(link, "label", f"{module_id} link")
            validate_url(require(link, "href", f"{module_id} link"), f"{module_id} link")

    for index, decision in enumerate(spec["decisions"], 1):
        decision_id = check_id(require(decision, "id", f"decision {index}"), {"D": PLAN_IDS["D"]}, f"decision {index}")
        ids.append(decision_id)
        for field in ("title", "tldr", "affects", "status"):
            require(decision, field, decision_id)
        status = str(decision["status"])
        if status not in {"Proposed", "Accepted"} and not re.fullmatch(r"Superseded \(by D-[0-9]{2,}\)", status):
            die(f"{decision_id}: invalid status {status!r}")
        validate_options(decision, decision_id)

    phase_numbers: list[int] = []
    covered: set[str] = set()
    for index, phase in enumerate(spec["phases"], 1):
        for field in ("number", "title", "delivers", "exit_criteria", "plan", "status"):
            require(phase, field, f"phase {index}")
        if not isinstance(phase["number"], int):
            die(f"phase {index}: number must be an integer")
        phase_numbers.append(phase["number"])
        if phase["status"] not in MODULE_STATUSES:
            die(f"phase {phase['number']}: invalid status {phase['status']!r}")
        if "progress" in phase and (not isinstance(phase["progress"], int) or not 0 <= phase["progress"] <= 100):
            die(f"phase {phase['number']}: progress must be integer 0–100")
        if "covers" not in phase:
            die(f"phase {phase['number']}: missing 'covers'; list the DoD IDs it satisfies, or []")
        check_refs(phase["covers"], {"DoD": PLAN_IDS["DoD"]}, set(dod_ids), f"phase {phase['number']} covers")
        covered.update(phase["covers"])
    if len(phase_numbers) != len(set(phase_numbers)):
        die("phases: duplicate phase numbers")
    ids.extend(f"P{number}" for number in phase_numbers)
    if spec["current_phase"] not in phase_numbers:
        die("plan: current_phase does not match any phase number")
    for module in spec["modules"]:
        if module["phase"] not in phase_numbers:
            die(f"{module['id']}: phase {module['phase']} does not exist")
    for dod_id in dod_ids:
        if dod_id not in covered:
            die(f"{dod_id}: no phase covers it; add it to one phase's 'covers'")

    risks = spec["risks_assumptions"]
    for field in ("risks", "assumptions"):
        if field not in risks:
            die(f"risks_assumptions: missing '{field}'")
    for index, risk in enumerate(risks["risks"], 1):
        for field in ("risk", "likelihood", "impact", "mitigation", "owner"):
            require(risk, field, f"risk {index}")
    for index, assumption in enumerate(risks["assumptions"], 1):
        require(assumption, "assumption", f"assumption {index}")
        status = require(assumption, "status", f"assumption {index}")
        if status not in ASSUMPTION_STATUSES:
            die(f"assumption {index}: invalid status {status!r}")
        verify_by = str(require(assumption, "verify_by", f"assumption {index}"))
        require(assumption, "owner", f"assumption {index}")
        if status == "Unverified" and re.fullmatch(r"\d{4}-\d{2}-\d{2}", verify_by) and verify_by < str(spec["updated"]):
            die(f"assumption {index}: still Unverified after verify_by {verify_by}; verify it or move it to risks")

    rollout = spec["rollout_rollback"]
    require(rollout, "steps", "rollout_rollback")
    require(rollout, "point_of_no_return", "rollout_rollback")
    for index, step in enumerate(rollout["steps"], 1):
        require(step, "label", f"rollout step {index}")
        require(step, "text", f"rollout step {index}")

    for index, question in enumerate(spec["open_questions"], 1):
        question_id = check_id(require(question, "id", f"question {index}"), {"Q": PLAN_IDS["Q"]}, f"question {index}")
        ids.append(question_id)
        for field in ("question", "owner", "due", "blocks"):
            require(question, field, question_id)
        if not question.get("options"):
            die(f"{question_id}: missing 'options'; give 2–4 answer choices with one recommended (free-text 'other' stays available)")
        validate_options(question, question_id)

    if len(ids) != len(set(ids)):
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        die(f"duplicate stable IDs: {', '.join(duplicates)}")
    known = set(ids)
    for decision in spec["decisions"]:
        check_refs(decision["affects"], PLAN_IDS, known, f"{decision['id']} affects")

    observability = spec["observability"]
    if "metrics" not in observability:
        die("observability: missing 'metrics'")
    for index, metric in enumerate(observability["metrics"], 1):
        for field in ("metric", "tracks_goal", "alert_when"):
            require(metric, field, f"metric {index}")
        check_refs(metric["tracks_goal"], {"G": PLAN_IDS["G"]}, known, f"metric {index} tracks_goal")

    if not spec["change_log"]:
        die("change_log: at least one entry is required")
    for index, change in enumerate(spec["change_log"], 1):
        for field in ("version", "date", "change"):
            require(change, field, f"change_log item {index}")


def status(value: object) -> str:
    return f'<span class="status {slug(value)}">{esc(value)}</span>'


def link(label: object, href: object) -> str:
    return f'<a href="{esc(validate_url(href, f"link {label!r}"))}">{inline(label)}</a>'


def table(headers: list[str], rows: list[list[str]], classes: list[str] | None = None) -> str:
    head = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body = []
    for index, row in enumerate(rows):
        row_class = f' class="{esc(classes[index])}"' if classes and classes[index] else ""
        body.append(f"<tr{row_class}>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    if not body:
        body.append(f'<tr><td colspan="{len(headers)}" class="empty">None.</td></tr>')
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def guide(spec: dict, key: str) -> str:
    text = spec.get("guides", {}).get(key)
    return f'<div class="guide" hidden><strong>Guide:</strong> {inline(text)}</div>' if text else ""


def section_start(number: str, title: str, subtitle: str, anchor: str, spec: dict, guide_key: str) -> str:
    return (
        f'<section class="section" id="{esc(anchor)}"><div class="section-head">'
        f'<h2>{esc(number + ". " if number else "")}{inline(title)}</h2>'
        f'<p class="kicker">{inline(subtitle)}</p></div>{guide(spec, guide_key)}'
    )


def render_fields(fields: list[dict]) -> str:
    if not fields:
        return '<p class="empty">No additional detail.</p>'
    return '<div class="fields">' + "".join(
        f'<div class="field"><div class="field-name">{inline(item.get("label", ""))}</div><div>{inline(item.get("text", ""))}</div></div>'
        for item in fields
    ) + "</div>"


def render_evidence(items: list[dict]) -> str:
    if not items:
        return ""
    parts = ['<div class="evidence">']
    for item in items:
        if item.get("label"):
            parts.append(f'<h4>{inline(item["label"])}</h4>')
        if item.get("code") is not None:
            source = f'{item.get("source")}\n' if item.get("source") else ""
            parts.append(f'<pre>{esc(source + str(item["code"]))}</pre>')
        if item.get("text"):
            parts.append(f'<p>{inline(item["text"])}</p>')
        if item.get("note"):
            parts.append(f'<div class="note">{inline(item["note"])}</div>')
    parts.append("</div>")
    return "".join(parts)


def render_options(item: dict) -> str:
    options = item.get("options")
    if not options:
        return ""
    item_id = str(item["id"])
    rows = []
    for option in options:
        badge = '<span class="recommended">my answer</span>' if option.get("recommended") else ""
        why = f'<span class="option-why">{inline(option["why"])}</span>' if option.get("why") else ""
        rows.append(
            f'<label class="option"><input data-choice type="radio" name="{esc(item_id)}" value="{esc(option["value"])}" '
            f'data-recommended="{str(bool(option.get("recommended"))).lower()}"><span>'
            f'<span class="option-title">{inline(option["title"])}{badge}</span>{why}</span></label>'
        )
    if item.get("other", True):
        rows.append(
            f'<label class="option"><input data-choice type="radio" name="{esc(item_id)}" value="{OTHER}" data-recommended="false">'
            f'<span><span class="option-title">Something else — I will say what</span>'
            f'<span class="option-why">Reject listed choices and type replacement decision.</span></span></label>'
            f'<textarea class="other" data-other="{esc(item_id)}" rows="2" hidden placeholder="Replacement decision or question."></textarea>'
        )
    return (
        f'<div class="choice-box" data-decision="{esc(item_id)}" data-title="{esc(item.get("title", item.get("question", "")))}">'
        '<h4>Reviewer choice</h4>' + "".join(rows) + "</div>"
    )


def render_sidebar(spec: dict) -> str:
    reviewers = "".join(f"<li>{inline(item)}</li>" for item in spec["reviewers"]) or '<li class="empty">None</li>'
    references = dict(spec["links"])
    technical = spec["system_shape"].get("technical_spec")
    if technical:
        references["Technical specification"] = technical["href"]
    links = "".join(link(str(label)[:1].upper() + str(label)[1:], href) for label, href in references.items()) or '<span class="empty">None</span>'
    nav = [
        ("summary", "30-second read"), ("business-context", "1. Business context"), ("goals-scope", "2. Goals and done"),
        ("system-shape", "3. System shape"), ("modules", "4. Workstreams"), ("decisions", "5. Key decisions"),
        ("phases", "6. Phases"), ("risks", "7. Risks and assumptions"), ("rollout", "8. Rollout and rollback"),
        ("observability", "9. Outcome metrics"), ("questions", "10. Open questions"), ("change-log", "11. Change log"),
    ]
    nav_html = "".join(f'<a href="#{anchor}">{esc(label)}</a>' for anchor, label in nav)
    return f'''<aside class="sidebar">
<div class="eyebrow">Implementation plan</div><h1>{inline(spec["title"])}</h1>{status(spec["status"])}
<div class="meta">
  <div class="meta-row"><span class="label">Version</span><span class="meta-value">{inline(spec["version"])}</span></div>
  <div class="meta-row"><span class="label">Updated</span><span class="meta-value">{esc(spec["updated"])}</span></div>
  <div class="meta-row"><span class="label">Owner</span><span class="meta-value">{inline(spec["owner"])}</span></div>
  <div class="meta-row"><span class="label">Reviewers</span><ul class="reviewers">{reviewers}</ul></div>
  <div class="meta-row"><span class="label">Links</span><div class="side-links">{links}</div></div>
</div><nav>{nav_html}</nav></aside>'''


def dod_counts(spec: dict) -> tuple[int, int]:
    items = spec["goals_scope"]["definition_of_done"]
    return sum(item["status"] == "verified" for item in items), len(items)


def render_summary(spec: dict) -> str:
    summary_rows = "".join(
        f'<div class="summary-row"><div class="summary-key">{esc(SUMMARY_LABELS[field])}</div><div>{inline(spec["summary"][field])}</div></div>'
        for field in SUMMARY_FIELDS
    )
    phases = spec["phases"]
    segments = []
    labels = []
    for phase in phases:
        current = phase["number"] == spec["current_phase"]
        progress = phase.get("progress", 100 if phase["status"] == "Done" else 0)
        css_class = "done" if phase["status"] == "Done" else "current" if current else ""
        style = f'flex:1;background:linear-gradient(90deg,var(--accent) {progress}%,var(--line-strong) {progress}%);' if current else "flex:1;"
        segments.append(f'<span class="progress-segment {css_class}" style="{style}" title="Phase {phase["number"]}: {esc(phase["status"])}"></span>')
        labels.append(f'<span class="{"current" if current else ""}">P{phase["number"]} {inline(phase["title"])}</span>')
    verified, total = dod_counts(spec)
    complete = " complete" if verified == total else ""
    return (
        '<section class="section" id="summary"><div class="section-head"><h2>The 30-second read</h2></div>'
        + guide(spec, "summary") + f'<div class="summary">{summary_rows}</div>'
        + f'<div class="progress"><div class="progress-meta"><span class="label">Phase progress</span>'
        + f'<a class="dod-count{complete}" href="#definition-of-done">DoD verified {verified} of {total}</a></div>'
        + f'<div class="progress-track">{"".join(segments)}</div>'
        + f'<div class="progress-labels" style="--phase-count:{len(phases)}">{"".join(labels)}</div></div></section>'
    )


def render_business(spec: dict) -> str:
    data = spec["business_context"]
    affected = "".join(f'<li><b>{inline(item["group"])}</b>: {inline(item["impact"])}</li>' for item in data["affected"])
    glossary = table(["Term", "Meaning"], [[inline(item["term"]), inline(item["meaning"])] for item in data["glossary"]])
    return (
        section_start("1", "Business context", "What hurts today, who it hurts, and why it is worth fixing now.", "business-context", spec, "business_context")
        + f'<h3>The problem</h3><p>{inline(data["problem"])}</p><h3>Who is affected</h3><ul class="clean-list">{affected}</ul>'
        + f'<h3>Why now</h3><p>{inline(data["why_now"])}</p><h3>Glossary</h3>{glossary}</section>'
    )


def render_dod(spec: dict) -> str:
    covered_in: dict[str, list[str]] = {}
    for phase in spec["phases"]:
        for dod_id in phase["covers"]:
            covered_in.setdefault(dod_id, []).append(f'P{phase["number"]}')
    items = []
    for item in spec["goals_scope"]["definition_of_done"]:
        verified = item["status"] == "verified"
        evidence = inline(item["evidence"]) if str(item.get("evidence") or "").strip() else '<span class="empty">Not verified yet.</span>'
        items.append(
            f'<li class="dod-item{" verified" if verified else ""}"><span class="dod-box" aria-hidden="true">{"✓" if verified else ""}</span>'
            f'<div class="dod-body"><div class="dod-head"><span class="fold-id">{esc(item["id"])}</span>'
            f'<span class="dod-condition">{inline(item["condition"])}</span>{status(item["status"])}</div>'
            f'<dl class="dod-meta"><dt>Verified by</dt><dd>{inline(item["verified_by"])}</dd><dt>Evidence</dt><dd>{evidence}</dd>'
            f'<dt>Phase</dt><dd>{esc(", ".join(covered_in.get(item["id"], [])))}</dd></dl></div></li>'
        )
    verified, total = dod_counts(spec)
    return (
        f'<h3 id="definition-of-done">Definition of done <span class="dod-count{" complete" if verified == total else ""}">{verified} of {total} verified</span></h3>'
        '<p class="note-line">Delivery is done when every item is verified. Outcome targets are checked later and do not block delivery.</p>'
        f'<ul class="dod">{"".join(items)}</ul>'
    )


def render_scope(spec: dict) -> str:
    data = spec["goals_scope"]
    outcomes = table(["ID", "Goal", "Baseline", "Target", "Measured by", "Check on"], [
        [esc(o["id"]), inline(o["goal"]), inline(o["baseline"]), inline(o["target"]), inline(o["measured_by"]), inline(o["check_on"])]
        for o in data["outcomes"]
    ])
    panels = []
    for title, key in (("In scope", "in_scope"), ("Out of scope", "out_of_scope"), ("Later", "later")):
        items = "".join(f"<li>{inline(item)}</li>" for item in data[key]) or '<li class="empty">None.</li>'
        panels.append(f'<div class="panel"><h3>{title}</h3><ul class="clean-list">{items}</ul></div>')
    return (
        section_start("2", "Goals and definition of done", "What is true after delivery, how delivery is proven, and where project edges sit.", "goals-scope", spec, "goals_scope")
        + f'<p class="goal-line"><b>Goal:</b> {inline(data["goal"])}</p><h3>Outcome targets</h3>{outcomes}{render_dod(spec)}'
        + f'<div class="grid-2" style="margin-top:14px">{"".join(panels)}</div></section>'
    )


def render_shape(spec: dict) -> str:
    data = spec["system_shape"]
    def flow(title: str, items: list[str]) -> str:
        return f'<div class="panel"><h3>{title}</h3><ol class="flow">' + "".join(f'<li><span>{inline(item)}</span></li>' for item in items) + "</ol></div>"
    technical = ""
    if data.get("technical_spec"):
        technical = f'<p>Technical detail: {link(data["technical_spec"]["label"], data["technical_spec"]["href"])}</p>'
    return section_start("3", "System shape", "Only change from today to end of v1.", "system-shape", spec, "system_shape") + f'<div class="grid-2">{flow("Today", data["today"])}{flow("After", data["after"])}</div>{technical}</section>'


def render_modules(spec: dict) -> str:
    technical_spec = spec["system_shape"].get("technical_spec")
    folds = []
    for module in spec["modules"]:
        refs = ", ".join(f"<code>{esc(ref)}</code>" for ref in module.get("technical_refs", []))
        if refs and technical_spec:
            refs += f' in {link(technical_spec["label"], technical_spec["href"])}'
        rows = (
            ("Phase", esc(module["phase"])),
            ("Owner", inline(module["owner"])),
            ("Delivers", inline(module["delivers"])),
            ("Depends on", inline(module["depends_on"]) if module.get("depends_on") else '<span class="empty">Nothing.</span>'),
            ("Exit criteria", inline(module["exit_criteria"])),
            ("Technical detail", refs or '<span class="empty">None.</span>'),
        )
        fields = '<div class="fields">' + "".join(
            f'<div class="field"><div class="field-name">{label}</div><div>{value}</div></div>' for label, value in rows
        ) + "</div>"
        links = ""
        if module.get("links"):
            links = '<div class="links">' + "".join(link(item["label"], item["href"]) for item in module["links"]) + "</div>"
        folds.append(
            f'<details class="fold"><summary><span class="fold-id">{esc(module["id"])}</span><span><span class="fold-title">{inline(module["title"])}</span>'
            f'<span class="tldr">{inline(module["tldr"])}</span></span>{status(module["status"])}</summary>'
            f'<div class="fold-body">{fields}{links}</div></details>'
        )
    body = "".join(folds) or '<p class="empty">No workstreams.</p>'
    return section_start("4", "Workstreams", "Delivery slices, owners, dependencies, and technical-spec links.", "modules", spec, "modules") + f'<div class="rows">{body}</div></section>'


def render_decisions(spec: dict) -> str:
    folds = []
    for decision in spec["decisions"]:
        affects = ", ".join(str(item) for item in decision["affects"])
        folds.append(
            f'<details class="fold"><summary><span class="fold-id">{esc(decision["id"])}</span><span><span class="fold-title">{inline(decision["title"])}</span>'
            f'<span class="tldr">{inline(decision["tldr"])}</span></span>{status(decision["status"])}</summary>'
            f'<div class="fold-body"><div class="field"><div class="field-name">Affects</div><div>{inline(affects)}</div></div>'
            f'{render_fields(decision.get("fields", []))}{render_evidence(decision.get("evidence", []))}{render_options(decision)}</div></details>'
        )
    body = "".join(folds) or '<p class="empty">No decisions.</p>'
    return section_start("5", "Key decisions", "Expensive-to-reverse choices, rejected paths, and revisit triggers.", "decisions", spec, "decisions") + f'<div class="rows">{body}</div></section>'


def render_phases(spec: dict) -> str:
    rows, classes = [], []
    for phase in spec["phases"]:
        current = phase["number"] == spec["current_phase"]
        phase_name = f'{"▶ " if current else ""}{phase["number"]}. {inline(phase["title"])}'
        covers = esc(", ".join(phase["covers"])) or '<span class="empty">—</span>'
        rows.append([phase_name, inline(phase["delivers"]), inline(phase["exit_criteria"]), covers, inline(phase["plan"]), inline(phase.get("actual", "")), status(phase["status"])])
        classes.append("current-phase" if current else "")
    return section_start("6", "Phases", "Work order; exit criteria, not code completion, close a phase.", "phases", spec, "phases") + table(["Phase", "Delivers", "Exit criteria", "Covers", "Plan", "Actual", "Status"], rows, classes) + "</section>"


def render_risks(spec: dict) -> str:
    data = spec["risks_assumptions"]
    risk_rows = []
    for risk in data["risks"]:
        likelihood = f'<span class="{"risk-high" if risk["likelihood"] == "High" else ""}">{inline(risk["likelihood"])}</span>'
        impact = f'<span class="{"risk-high" if risk["impact"] == "High" else ""}">{inline(risk["impact"])}</span>'
        risk_rows.append([inline(risk["risk"]), likelihood, impact, inline(risk["mitigation"]), inline(risk["owner"])])
    assumptions = [[inline(item["assumption"]), status(item["status"]), inline(item["verify_by"]), inline(item["owner"])] for item in data["assumptions"]]
    return section_start("7", "Risks and assumptions", "Delivery risks, owned responses, and beliefs still needing proof.", "risks", spec, "risks_assumptions") + table(["Risk", "Likelihood", "Impact", "Mitigation", "Owner"], risk_rows) + "<h3>Assumptions</h3>" + table(["Assumption", "Status", "Verify by", "Owner"], assumptions) + "</section>"


def render_rollout(spec: dict) -> str:
    data = spec["rollout_rollback"]
    items = "".join(f'<li><b>{inline(step["label"])}</b>: {inline(step["text"])}</li>' for step in data["steps"])
    return section_start("8", "Rollout and rollback", "Safe production path, data behavior, and irreversible boundary.", "rollout", spec, "rollout_rollback") + f'<ul class="clean-list">{items}</ul><div class="point-no-return"><b>Point of no return:</b> {inline(data["point_of_no_return"])}</div></section>'


def render_observability(spec: dict) -> str:
    goals = {item["id"]: item["goal"] for item in spec["goals_scope"]["outcomes"]}
    metrics = [
        [f'<code>{esc(item["metric"])}</code>', "<br>".join(f"{esc(goal_id)} {inline(goals[goal_id])}" for goal_id in item["tracks_goal"]), inline(item["alert_when"])]
        for item in spec["observability"]["metrics"]
    ]
    return section_start("9", "Outcome metrics and observability", "Signals that track outcome targets after release.", "observability", spec, "observability") + table(["Metric", "Tracks goal", "Alert when"], metrics) + "</section>"


def render_questions(spec: dict) -> str:
    questions = spec["open_questions"]
    rows = [[esc(q["id"]), inline(q["question"]), inline(q["owner"]), inline(q["due"]), inline(q["blocks"])] for q in questions]
    cards = []
    for question in questions:
        cards.append(
            f'<div class="panel"><div class="fold-id">{esc(question["id"])}</div><h3>{inline(question["question"])}</h3>'
            f'<div class="question-meta"><span><b>Owner:</b> {inline(question["owner"])}</span><span><b>Due:</b> {inline(question["due"])}</span><span><b>Blocks:</b> {inline(question["blocks"])}</span></div>'
            f'{render_evidence(question.get("evidence", []))}{render_options(question)}</div>'
        )
    interactive = '<h3>Answer in browser</h3><div class="rows">' + "".join(cards) + "</div>" if cards else ""
    return section_start("10", "Open questions", "Unknowns with owners, due dates, and blocked work.", "questions", spec, "open_questions") + table(["#", "Question", "Owner", "Due", "Blocks"], rows) + interactive + "</section>"


def render_change_log(spec: dict) -> str:
    rows = [[inline(item["version"]), inline(item["date"]), inline(item["change"])] for item in spec["change_log"]]
    return section_start("11", "Change log", "Scope, decision, estimate, and exit-criteria history; newest first.", "change-log", spec, "change_log") + table(["Version", "Date", "Change"], rows) + "</section>"


def build(spec: dict) -> str:
    validate(spec)
    css = (ASSETS / "plan.css").read_text()
    js = (ASSETS / "plan.js").read_text()
    key = spec.get("key") or f'{slug(spec["title"])}-{spec["updated"]}-v{slug(spec["version"])}'
    filename = spec.get("answers_filename") or f'{slug(spec["title"])}-answers.md'
    sections = "".join((
        render_summary(spec), render_business(spec), render_scope(spec), render_shape(spec), render_modules(spec), render_decisions(spec), render_phases(spec), render_risks(spec), render_rollout(spec),
        render_observability(spec), render_questions(spec), render_change_log(spec),
    ))
    return f'''<!doctype html>
<html lang="{esc(spec.get("lang", "en"))}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(spec["title"])}</title><style>{css}</style></head><body><div class="shell">{render_sidebar(spec)}<main class="content">
<header class="hero"><h1>{inline(spec["title"])}</h1><p class="tagline">{inline(spec["tagline"])}</p><div class="toolbar">
<button class="primary" onclick="copyAnswers()">Copy review answers</button><button onclick="downloadAnswers()">Download answers</button>
<button onclick="acceptAll()">Accept recommendations</button><button onclick="toggleGuides()">Writing guides</button><button onclick="toggleTheme()">Light / dark</button><button onclick="clearAnswers()">Clear answers</button>
</div><p class="flash" id="flash" hidden></p></header>{sections}
<section class="section answer-panel"><div class="section-head"><h2>Anything missed?</h2><p class="kicker">Questions, context, or decisions not represented above.</p></div>
<textarea class="other" id="review-notes" rows="3" placeholder="Free text; included in answer export."></textarea><h3>Your answers</h3>
<textarea class="answers" id="answers" readonly></textarea><div class="toolbar"><button class="primary" onclick="copyAnswers()">Copy review answers</button><button onclick="downloadAnswers()">Download answers</button></div></section>
<footer class="footer">Source: structured implementation plan v{inline(spec["version"])}. Answers stay in this browser until copied or downloaded.</footer>
</main></div><script>const KEY={safe_json(key)};const TITLE={safe_json(spec["title"])};const FILENAME={safe_json(filename)};{js}</script></body></html>'''


def main(argv: list[str]) -> None:
    if len(argv) != 3:
        sys.exit(__doc__)
    source, output = map(Path, argv[1:])
    try:
        spec = json.loads(source.read_text())
        rendered = build(spec)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        sys.exit(f"build.py: {error}")
    choices = sum(bool(item.get("options")) for item in spec["decisions"] + spec["open_questions"])
    verified, total = dod_counts(spec)
    print(f"{output} — {len(spec['modules'])} workstream(s), {len(spec['decisions'])} decision(s), {choices} browser choice(s), DoD verified {verified} of {total}")


if __name__ == "__main__":
    main(sys.argv)
