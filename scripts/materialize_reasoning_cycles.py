#!/usr/bin/env python3
"""Materialize and audit the 400 source-authored Palamedes reasoning cycles.

Later empirical cycles may coexist in the output directory. They are authored
from observed runs rather than generated from the four source documents and are
therefore outside this materializer's equality audit.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCES = (
    ROOT / "docs/inquiry/2026-07-25-reasoning-cycles-001-100.md",
    ROOT / "docs/inquiry/2026-07-25-reasoning-cycles-101-200.md",
    ROOT / "docs/inquiry/2026-07-25-reasoning-cycles-201-300.md",
    ROOT / "docs/inquiry/2026-07-25-reasoning-cycles-301-400.md",
)
OUTPUT_DIR = ROOT / "docs/inquiry/reasoning-cycles"
INDEX = OUTPUT_DIR / "README.md"
REQUIRED_LABELS = (
    "## Inherited view",
    "## New pressure",
    "## Resulting view",
    "## Next question",
    "## Lineage",
)


def normalize(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def authored_cycles() -> list[str]:
    cycles: list[str] = []
    expected_number = 1
    for source in SOURCES:
        text = source.read_text(encoding="utf-8")
        main = re.split(r"(?m)^## (?:What changed|Change from cycle)", text, maxsplit=1)[0]
        matches = list(re.finditer(r"(?m)^(\d+)\.\s+", main))
        for index, match in enumerate(matches):
            number = int(match.group(1))
            if number != expected_number:
                raise RuntimeError(f"expected authored cycle {expected_number}, found {number}")
            end = matches[index + 1].start() if index + 1 < len(matches) else len(main)
            body = main[match.end() : end]
            body = re.split(r"(?m)^##\s+", body, maxsplit=1)[0]
            cycles.append(normalize(body))
            expected_number += 1
    return cycles


def first_clause(text: str) -> str:
    return re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0].strip()


def final_clause(text: str) -> str:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return parts[-1]


def next_record_name(number: int, generated_count: int) -> str:
    if number == 100:
        return "owner-correction.md"
    if number < generated_count:
        return f"cycle-{number + 1:03d}.md"
    empirical_successor = OUTPUT_DIR / f"cycle-{number + 1:03d}.md"
    return empirical_successor.name if empirical_successor.is_file() else "current-conclusion.md"


def record(number: int, cycles: list[str]) -> str:
    current = cycles[number - 1]
    if number == 1:
        inherited = (
            "The inquiry starts from the hypothesis that Palamedes should replace "
            "human upstream thinking by producing the best answer."
        )
    elif number == 101:
        inherited = (
            "The owner corrected cycle 100: Palamedes must replace routine human "
            "problem discovery, purpose formation, value comparison, and mission selection."
        )
    else:
        inherited = final_clause(cycles[number - 2])
    resulting = final_clause(current)
    if number == 100:
        next_question = (
            "How does the owner's correction change the remaining assumption that "
            "value-bearing commitments return to a human?"
        )
    elif number < len(cycles):
        next_question = (
            "What breaks or becomes newly possible if the next cycle pressures this result: "
            f"{first_clause(cycles[number])}"
        )
    else:
        next_question = (
            "Can Palamedes independently originate a mission worth planning that equal-budget "
            "human and one-shot-agent baselines do not produce?"
        )
    source_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
    return "\n".join(
        [
            f"# Palamedes Reasoning Cycle {number:03d}",
            "",
            "Date: 2026-07-25",
            "Thinker: Codex acting as Palamedes",
            "External model calls: none",
            "",
            "## Inherited view",
            "",
            inherited,
            "",
            "## New pressure",
            "",
            current,
            "",
            "## Resulting view",
            "",
            resulting,
            "",
            "## Next question",
            "",
            next_question,
            "",
            "## Lineage",
            "",
            f"- previous: `{'origin' if number == 1 else 'owner-correction.md' if number == 101 else f'cycle-{number - 1:03d}.md'}`",
            f"- next: `{next_record_name(number, len(cycles))}`",
            f"- authored-source-sha256: `{source_hash}`",
            "",
        ]
    )


def index_text(cycles: list[str]) -> str:
    lines = [
        f"# Palamedes Reasoning Cycle Records 001–{len(cycles):03d}",
        "",
        f"These are {len(cycles)} separately materialized records of one continuous reasoning",
        "process. The contents were authored as dependent reasoning moves before this",
        "mechanical split; the materializer does not generate the thoughts.",
        "",
        "| Cycle | Inherited from | Pressure summary |",
        "| ---: | --- | --- |",
    ]
    for number, body in enumerate(cycles, start=1):
        previous = "origin" if number == 1 else "owner correction" if number == 101 else f"{number - 1:03d}"
        summary = first_clause(body).replace("|", "\\|")
        lines.append(f"| [{number:03d}](cycle-{number:03d}.md) | {previous} | {summary} |")
    lines.extend(
        [
            "",
            "Between cycles 100 and 101, the owner's correction is preserved in",
            "[`owner-correction.md`](owner-correction.md). The current result after",
            f"cycle {len(cycles)} is summarized in [`current-conclusion.md`](current-conclusion.md).",
            "",
        ]
    )
    return "\n".join(lines)


def owner_correction() -> str:
    return """# Owner Correction After Cycle 100

Date: 2026-07-25

## Correction

Cycle 100 still assumed that Palamedes should return value-laden or irreversible
commitments to a human. The owner clarified that Palamedes is intended to replace
the remaining human upstream cognition before planner, task, and implementation:
problem discovery, purpose formation, value comparison, and mission selection.

## Resulting view

Palamedes is an autonomous pre-planner. It originates a mission under delegated
constitutional authority and hands a mission contract to downstream planning
agents. Routine value-bearing judgment is part of its job, not a mandatory human
checkpoint.

## New unresolved problem

How can Palamedes originate worthwhile purposes without collapsing into proxy
optimization, owner imitation, or authority without accountability?

## Next artifact

[`cycle-101.md`](cycle-101.md)
"""


def current_conclusion() -> str:
    return """# Current Conclusion After Cycle 400

Build five bounded artifacts in order: mission schemas, intent-specific state
commands, a provider-neutral MissionCycle, one adversarial sequential replay,
and a traceable planner handoff.

This is the smallest contact with reality capable of falsifying the 400-cycle
thesis. Anything broader before that would conceal whether Palamedes can
actually originate a worthwhile mission.

See [`../../palamedes-pre-planner-contract.md`](../../palamedes-pre-planner-contract.md).
"""


def write_records() -> None:
    cycles = authored_cycles()
    expected_count = len(SOURCES) * 100
    if len(cycles) != expected_count:
        raise RuntimeError(f"expected {expected_count} authored cycles, found {len(cycles)}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for number in range(1, expected_count + 1):
        (OUTPUT_DIR / f"cycle-{number:03d}.md").write_text(record(number, cycles), encoding="utf-8")
    INDEX.write_text(index_text(cycles), encoding="utf-8")
    (OUTPUT_DIR / "owner-correction.md").write_text(owner_correction(), encoding="utf-8")
    (OUTPUT_DIR / "current-conclusion.md").write_text(current_conclusion(), encoding="utf-8")


def audit() -> list[str]:
    errors: list[str] = []
    cycles = authored_cycles()
    expected_count = len(SOURCES) * 100
    generated_names = {
        f"cycle-{number:03d}.md" for number in range(1, expected_count + 1)
    }
    files = sorted(
        path for path in OUTPUT_DIR.glob("cycle-*.md") if path.name in generated_names
    )
    if len(cycles) != expected_count:
        errors.append(f"source_cycle_count={len(cycles)}")
    if len(files) != expected_count:
        errors.append(f"record_file_count={len(files)}")
    expected_names = [f"cycle-{number:03d}.md" for number in range(1, expected_count + 1)]
    if [path.name for path in files] != expected_names:
        errors.append(f"generated cycle filenames are not contiguous 001-{expected_count}")
    content_hashes: set[str] = set()
    for number, path in enumerate(files, start=1):
        text = path.read_text(encoding="utf-8")
        for label in REQUIRED_LABELS:
            if label not in text:
                errors.append(f"{path.name}: missing {label}")
        if f"Cycle {number:03d}" not in text:
            errors.append(f"{path.name}: header mismatch")
        previous_name = "origin" if number == 1 else "owner-correction.md" if number == 101 else f"cycle-{number - 1:03d}.md"
        next_name = next_record_name(number, expected_count)
        if f"- previous: `{previous_name}`" not in text:
            errors.append(f"{path.name}: previous link mismatch")
        if f"- next: `{next_name}`" not in text:
            errors.append(f"{path.name}: next link mismatch")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in content_hashes:
            errors.append(f"{path.name}: duplicate record content")
        content_hashes.add(digest)
        expected = record(number, cycles)
        if text != expected:
            errors.append(f"{path.name}: differs from authored source")
    if not INDEX.is_file():
        errors.append("index missing")
    else:
        index = INDEX.read_text(encoding="utf-8")
        for number in range(1, expected_count + 1):
            if f"(cycle-{number:03d}.md)" not in index:
                errors.append(f"index missing cycle-{number:03d}.md")
    if not (OUTPUT_DIR / "owner-correction.md").is_file():
        errors.append("owner correction missing")
    if not (OUTPUT_DIR / "current-conclusion.md").is_file():
        errors.append("current conclusion missing")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        write_records()
    errors = audit()
    print(
        f"source_cycles={len(authored_cycles())} record_files={len(list(OUTPUT_DIR.glob('cycle-*.md')))} "
        f"errors={len(errors)}"
    )
    for error in errors:
        print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
