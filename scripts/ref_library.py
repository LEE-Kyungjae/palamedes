#!/usr/bin/env python3
"""Manage a centralized, provenance-preserving reference library."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse


PATTERN_KEYWORDS = {
    "agent_loop": ("agent loop", "reasoning loop", "tool-calling loop", "run_once"),
    "memory": ("memory", "scratchpad", "context compact", "context-save"),
    "permissions": ("permission", "approval", "sandbox", "capability"),
    "wake_runtime": ("heartbeat", "wake", "background task", "scheduler"),
    "evaluation": ("eval", "benchmark", "self-validation", "observability"),
    "skills": ("skill.md", "skills", "plugin"),
}
DOC_NAMES = ("README.md", "AGENTS.md", "ARCHITECTURE.md", "VISION.md", "DESIGN.md")


def run_git(repo: Path, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def normalize_remote(remote: str) -> str:
    value = remote.strip()
    if value.startswith("git@github.com:"):
        value = f"https://github.com/{value.removeprefix('git@github.com:')}"
    if value.endswith(".git"):
        value = value[:-4]
    return value.rstrip("/").lower()


def remote_slug(remote: str) -> str:
    normalized = normalize_remote(remote)
    parsed = urlparse(normalized)
    if parsed.scheme and parsed.netloc:
        path = parsed.path.strip("/")
        return f"{parsed.netloc}/{path}" if path else parsed.netloc
    return normalized.replace(":", "/").strip("/")


def discover_git_repos(root: Path) -> list[Path]:
    repos: list[Path] = []
    for git_entry in root.rglob(".git"):
        if git_entry.is_dir() or git_entry.is_file():
            repos.append(git_entry.parent)
    return sorted(set(repos))


@dataclass(frozen=True)
class RepoState:
    path: str
    remote: str
    normalized_remote: str
    branch: str
    head: str
    upstream: str
    dirty: int
    ahead: int
    behind: int

    @property
    def aligned(self) -> bool:
        return self.dirty == 0 and self.ahead == 0 and self.behind == 0


def _git_value(repo: Path, *args: str) -> str:
    result = run_git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def inspect_repo(repo: Path) -> RepoState:
    remote = _git_value(repo, "remote", "get-url", "origin")
    counts = _git_value(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
    ahead, behind = (0, 0)
    if counts:
        parts = counts.split()
        if len(parts) == 2:
            ahead, behind = map(int, parts)
    dirty_output = _git_value(repo, "status", "--porcelain=v1", "-uno")
    return RepoState(
        path=str(repo),
        remote=remote,
        normalized_remote=normalize_remote(remote),
        branch=_git_value(repo, "branch", "--show-current"),
        head=_git_value(repo, "rev-parse", "HEAD"),
        upstream=_git_value(repo, "rev-parse", "--abbrev-ref", "@{upstream}"),
        dirty=len(dirty_output.splitlines()) if dirty_output else 0,
        ahead=ahead,
        behind=behind,
    )


def duplicate_groups(states: Iterable[RepoState]) -> dict[str, list[RepoState]]:
    groups: dict[str, list[RepoState]] = {}
    for state in states:
        if state.normalized_remote:
            groups.setdefault(state.normalized_remote, []).append(state)
    return {remote: items for remote, items in groups.items() if len(items) > 1}


def update_repo(repo: Path) -> tuple[bool, str]:
    state = inspect_repo(repo)
    if state.dirty:
        return False, f"preserved: {state.dirty} tracked modification(s)"
    result = run_git(repo, "pull", "--ff-only")
    message = (result.stdout or result.stderr).strip().splitlines()
    return result.returncode == 0, message[0] if message else ""


def _candidate_docs(repo: Path) -> list[Path]:
    docs = [repo / name for name in DOC_NAMES if (repo / name).is_file()]
    for directory in ("docs", "src"):
        base = repo / directory
        if not base.is_dir():
            continue
        for current, directories, filenames in os.walk(base):
            directories[:] = [
                name
                for name in directories
                if name not in {".git", "node_modules", "dist", "build", ".venv", "vendor"}
            ]
            current_path = Path(current)
            docs.extend(current_path / name for name in filenames if name in DOC_NAMES)
            if len(docs) >= 30:
                break
    return sorted(set(docs))[:30]


def catalog_repo(state: RepoState) -> dict[str, object]:
    repo = Path(state.path)
    matches: dict[str, list[str]] = {key: [] for key in PATTERN_KEYWORDS}
    docs = _candidate_docs(repo)
    for document in docs:
        try:
            text = document.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        relative = str(document.relative_to(repo))
        for category, keywords in PATTERN_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                matches[category].append(relative)
    return {
        "name": repo.name,
        "path": state.path,
        "remote": state.remote,
        "head": state.head,
        "patterns": {key: value for key, value in matches.items() if value},
        "documents_scanned": [str(path.relative_to(repo)) for path in docs],
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/Users/ze/work/ref/roots"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Inspect repositories and duplicate remotes.")
    status.add_argument("--json", dest="json_path", type=Path)

    update = subparsers.add_parser("update", help="Fast-forward clean repositories.")
    update.add_argument("--json", dest="json_path", type=Path)

    catalog = subparsers.add_parser("catalog", help="Build an agent-pattern catalog.")
    catalog.add_argument("--output", type=Path, required=True)
    return parser


def _states(root: Path) -> list[RepoState]:
    return [inspect_repo(repo) for repo in discover_git_repos(root)]


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    states = _states(args.root)
    if args.command == "status":
        result = {
            "root": str(args.root),
            "repository_count": len(states),
            "aligned_count": sum(state.aligned for state in states),
            "repositories": [asdict(state) for state in states],
            "duplicate_groups": {
                remote: [item.path for item in items]
                for remote, items in duplicate_groups(states).items()
            },
        }
        if args.json_path:
            write_json(args.json_path, result)
        print(
            f"repositories={result['repository_count']} "
            f"aligned={result['aligned_count']} "
            f"duplicate_groups={len(result['duplicate_groups'])}"
        )
        return 0
    if args.command == "update":
        updates = []
        for state in states:
            ok, message = update_repo(Path(state.path))
            updates.append({"path": state.path, "ok": ok, "message": message})
        if args.json_path:
            write_json(args.json_path, updates)
        failed = sum(not item["ok"] for item in updates)
        print(f"repositories={len(updates)} failed={failed}")
        return 1 if failed else 0
    if args.command == "catalog":
        catalog = [catalog_repo(state) for state in states]
        write_json(args.output, catalog)
        print(f"repositories={len(catalog)} output={args.output}")
        return 0
    raise AssertionError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
