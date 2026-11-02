#!/usr/bin/env python3
"""Smoke-test implementation plan renderer with bundled example."""

from __future__ import annotations

import copy
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "scripts" / "build.py"
EXAMPLE = ROOT / "reference" / "example.json"


def run(source: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(BUILDER), str(source), str(output)],
        check=False,
        capture_output=True,
        text=True,
    )


def rejected(base: dict, mutate, expected: str, directory: Path) -> None:
    spec = copy.deepcopy(base)
    mutate(spec)
    source = directory / "invalid.json"
    output = directory / "invalid.html"
    source.write_text(json.dumps(spec))
    result = run(source, output)
    assert result.returncode != 0, f"invalid source passed: {expected}"
    assert expected in result.stderr, result.stderr


def main() -> None:
    base = json.loads(EXAMPLE.read_text())
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        output = directory / "plan.html"
        result = run(EXAMPLE, output)
        assert result.returncode == 0, result.stderr
        page = output.read_text()
        assert page.startswith("<!doctype html>")
        assert "<link" not in page and "<script src=" not in page
        assert "https://" not in page and "http://" not in page
        assert page.count('class="section" id=') == 12
        headings = ["1. Business context", "2. Goals and definition of done", "4. Workstreams", "9. Outcome metrics and observability", "11. Change log"]
        positions = [page.index(f"<h2>{heading}") for heading in headings]
        assert positions == sorted(positions), headings
        assert "DoD verified 1 of 5" in page
        assert 'data-decision="D-03"' in page
        assert 'data-decision="Q1"' in page
        assert "localStorage.setItem(KEY" in page
        assert "Accept recommendations" in page
        hero = page.split('<header class="hero">', 1)[1].split('</header>', 1)[0]
        assert './technical-spec.html' not in hero
        sidebar = page.split('<main class="content">', 1)[0]
        assert 'Technical specification</a>' in sidebar and './technical-spec.html' in sidebar
        with_diagrams = copy.deepcopy(base)
        with_diagrams['links']['diagram reference'] = './diagrams.md'
        diagram_source = directory / 'diagrams-plan.json'
        diagram_source.write_text(json.dumps(with_diagrams))
        assert run(diagram_source, directory / 'diagrams-plan.html').returncode == 0
        assert 'href="./diagrams.md"' in (directory / 'diagrams-plan.html').read_text().split('<main class="content">', 1)[0]
        plan_only = copy.deepcopy(base)
        plan_only['system_shape'].pop('technical_spec', None)
        source = directory / 'plan-only.json'
        source.write_text(json.dumps(plan_only))
        assert run(source, directory / 'plan-only.html').returncode == 0
        assert 'Technical specification:' not in (directory / 'plan-only.html').read_text().split('</header>', 1)[0]

        dod = lambda s: s["goals_scope"]["definition_of_done"]
        rejected(base, lambda s: s.update(status="review"), "invalid status", directory)
        rejected(base, lambda s: s.update(current_phase=99), "current_phase", directory)
        rejected(base, lambda s: s["modules"][0].update(tldr=""), "empty 'tldr'", directory)
        rejected(base, lambda s: s["links"].update(repo="javascript:alert(1)"), "unsafe URL scheme", directory)
        rejected(base, lambda s: s["decisions"][1]["options"][0].update(recommended=False), "exactly one recommended", directory)
        rejected(base, lambda s: s["open_questions"][0].update(id="Q2"), "duplicate stable IDs", directory)
        rejected(base, lambda s: dod(s)[1].update(verified_by=""), "DoD-2: empty 'verified_by'", directory)
        rejected(base, lambda s: s["phases"][3].update(covers=["DoD-4"]), "DoD-5: no phase covers it", directory)
        rejected(base, lambda s: s["phases"][1].update(covers=["DoD-1", "DoD-9"]), "unknown ID 'DoD-9'", directory)
        rejected(base, lambda s: dod(s)[0].update(evidence=""), "DoD-1: status 'verified' needs non-empty 'evidence'", directory)
        rejected(base, lambda s: s["modules"][0].update(technical_refs=["SPEC-01"]), "unregistered ID prefix 'SPEC'", directory)
        rejected(base, lambda s: s["goals_scope"]["outcomes"][0].update(id="O1"), "unregistered ID prefix 'O'", directory)
        rejected(base, lambda s: s.update(status="shipped"), "needs every DoD item verified", directory)
        rejected(base, lambda s: s["risks_assumptions"]["assumptions"][1].update(verify_by="2026-10-01"), "still Unverified after verify_by", directory)
        rejected(base, lambda s: s.update(verification=s.pop("observability")), "'verification' was renamed to 'observability'", directory)
        rejected(base, lambda s: s["open_questions"][1].pop("options"), "Q2: missing 'options'", directory)

    print("implementation-review smoke test: PASS")


if __name__ == "__main__":
    main()
