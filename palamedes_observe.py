#!/usr/bin/env python3
"""Bounded, provenance-bearing observation of a Palamedes workspace."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


MAX_DOCUMENT_BYTES = 24_000
MAX_TOTAL_DOCUMENT_BYTES = 120_000
MAX_DOCUMENTS = 12
MAX_TODOS = 50
MAX_REF_REPOS = 60
MAX_REF_KNOWLEDGE_REPOS = 16
MAX_REF_KNOWLEDGE_BYTES = 4_000
DEFAULT_DOCUMENT_NAMES = (
    "AGENTS.md",
    "README.md",
    "PALAMEDES_INQUIRY.md",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
)
OBSERVE_CONFIG_PATH = Path(".palamedes/observe.json")
SENSITIVE_NAME_PATTERNS = (
    ".env",
    "credentials",
    "secret",
    "private_key",
    "id_rsa",
    "id_ed25519",
)
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(
        r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*['\"]?([^\s'\"]{8,})"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def redact(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        if pattern.groups >= 2:
            result = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", result)
        else:
            result = pattern.sub("[REDACTED]", result)
    return result


def safe_document(path: Path) -> bool:
    lowered_parts = [part.lower() for part in path.parts]
    return not any(
        pattern in part
        for part in lowered_parts
        for pattern in SENSITIVE_NAME_PATTERNS
    )


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 10,
) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            list(args),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "NO_COLOR": "1"},
        )
        return {
            "command": list(args),
            "returncode": completed.returncode,
            "stdout": redact(completed.stdout[:24_000]),
            "stderr": redact(completed.stderr[:8_000]),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(args),
            "returncode": None,
            "stdout": redact(str(exc.stdout or "")[:24_000]),
            "stderr": redact(str(exc.stderr or "")[:8_000]),
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": list(args),
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timed_out": False,
        }


def discover_documents(workspace: Path) -> List[Path]:
    found: List[Path] = []
    for name in DEFAULT_DOCUMENT_NAMES:
        candidate = workspace / name
        if candidate.is_file() and safe_document(candidate):
            found.append(candidate)
    docs = workspace / "docs"
    if docs.is_dir():
        for candidate in sorted(docs.glob("*.md")):
            if safe_document(candidate):
                found.append(candidate)
            if len(found) >= MAX_DOCUMENTS:
                break
    config_path = workspace / OBSERVE_CONFIG_PATH
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config = {}
        configured = config.get("documents", []) if isinstance(config, dict) else []
        if isinstance(configured, list):
            workspace_root = workspace.resolve()
            for raw_path in configured:
                if not isinstance(raw_path, str) or not raw_path.strip():
                    continue
                candidate = (workspace / raw_path).resolve()
                try:
                    candidate.relative_to(workspace_root)
                except ValueError:
                    continue
                if candidate.is_file() and safe_document(candidate):
                    found.append(candidate)
    unique: List[Path] = []
    seen = set()
    for candidate in found:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(candidate)
    return unique[:MAX_DOCUMENTS]


def observe_documents(workspace: Path) -> Dict[str, Any]:
    items = []
    total = 0
    for path in discover_documents(workspace):
        remaining = MAX_TOTAL_DOCUMENT_BYTES - total
        if remaining <= 0:
            break
        allowed = min(MAX_DOCUMENT_BYTES, remaining)
        raw = path.read_bytes()
        excerpt_bytes = raw[:allowed]
        text = excerpt_bytes.decode("utf-8", errors="replace")
        redacted = redact(text)
        headings = [
            line.strip()
            for line in redacted.splitlines()
            if line.lstrip().startswith("#")
        ][:30]
        item = {
            "path": str(path.relative_to(workspace)),
            "source_type": "workspace_document",
            "size_bytes": len(raw),
            "content_sha256": hashlib.sha256(raw).hexdigest(),
            "excerpt": redacted,
            "excerpt_truncated": len(raw) > len(excerpt_bytes),
            "headings": headings,
        }
        item["observation_fingerprint"] = fingerprint(item)
        items.append(item)
        total += len(excerpt_bytes)
    return {
        "documents": items,
        "document_count": len(items),
        "excerpt_bytes": total,
        "bounded": True,
    }


def observe_git(workspace: Path) -> Dict[str, Any]:
    inside = run_command(["git", "rev-parse", "--is-inside-work-tree"], cwd=workspace)
    if inside["returncode"] != 0 or inside["stdout"].strip() != "true":
        return {"available": False, "reason": "not_a_git_worktree"}
    head = run_command(["git", "rev-parse", "HEAD"], cwd=workspace)
    branch = run_command(["git", "branch", "--show-current"], cwd=workspace)
    status = run_command(["git", "status", "--short"], cwd=workspace)
    diff_stat = run_command(["git", "diff", "--stat"], cwd=workspace)
    recent = run_command(
        ["git", "log", "-5", "--pretty=format:%H%x09%aI%x09%s"], cwd=workspace
    )
    return {
        "available": True,
        "head": head["stdout"].strip(),
        "branch": branch["stdout"].strip(),
        "status": status["stdout"].splitlines()[:200],
        "diff_stat": diff_stat["stdout"].splitlines()[:200],
        "recent_commits": recent["stdout"].splitlines()[:5],
        "commands_ok": all(
            item["returncode"] == 0
            for item in (head, branch, status, diff_stat, recent)
        ),
    }


def _iter_source_files(workspace: Path) -> Iterable[Path]:
    ignored = {".git", ".palamedes", "node_modules", "vendor", ".venv", "venv"}
    suffixes = {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".md",
        ".toml",
        ".yaml",
        ".yml",
    }
    count = 0
    for path in workspace.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if not safe_document(path) or path.stat().st_size > 1_000_000:
            continue
        yield path
        count += 1
        if count >= 500:
            return


def observe_todos(workspace: Path) -> Dict[str, Any]:
    markers = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b[:\s-]*(.*)", re.IGNORECASE)
    items = []
    for path in _iter_source_files(workspace):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            match = markers.search(line)
            if not match:
                continue
            items.append(
                {
                    "path": str(path.relative_to(workspace)),
                    "line": number,
                    "marker": match.group(1).upper(),
                    "text": redact(match.group(2).strip())[:500],
                }
            )
            if len(items) >= MAX_TODOS:
                return {"items": items, "truncated": True}
    return {"items": items, "truncated": False}


def observe_palamedes_state(workspace: Path) -> Dict[str, Any]:
    state = workspace / ".palamedes"
    paths = {
        "plan": state / "plan.json",
        "events": state / "events.jsonl",
        "revisions": state / "revisions.jsonl",
        "outcomes": state / "missions" / "outcomes.jsonl",
    }
    result: Dict[str, Any] = {}
    for name, path in paths.items():
        if not path.is_file():
            result[name] = {"available": False}
            continue
        raw = path.read_bytes()
        item: Dict[str, Any] = {
            "available": True,
            "path": str(path.relative_to(workspace)),
            "size_bytes": len(raw),
            "content_sha256": hashlib.sha256(raw).hexdigest(),
        }
        if name == "plan":
            try:
                plan = json.loads(raw)
            except json.JSONDecodeError:
                plan = {}
            item["summary"] = {
                "goal": str(plan.get("goal", ""))[:1000],
                "success_metric": str(plan.get("success_metric", ""))[:1000],
                "evidence_count": len(plan.get("evidence", [])),
                "open_hypothesis_count": sum(
                    1
                    for entry in plan.get("hypothesis_log", [])
                    if isinstance(entry, dict) and entry.get("status") == "open"
                ),
                "planned_probe_count": sum(
                    1
                    for entry in plan.get("development_probes", [])
                    if isinstance(entry, dict) and entry.get("status") == "planned"
                ),
            }
        else:
            item["record_count"] = len(raw.splitlines())
        result[name] = item
    return result


def observe_ref_root(ref_root: Optional[Path]) -> Dict[str, Any]:
    if ref_root is None or not ref_root.is_dir():
        return {
            "available": False,
            "path": str(ref_root) if ref_root else "",
            "repositories": [],
        }
    scan_root = ref_root / "roots" if (ref_root / "roots").is_dir() else ref_root
    repositories = []
    candidates: List[Path] = []
    manifest = ref_root / "manifests" / "status-current.json"
    if manifest.is_file():
        try:
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            rows = payload.get("repositories", []) if isinstance(payload, dict) else []
            candidates = sorted(
                {
                    Path(item["path"]).expanduser()
                    for item in rows
                    if isinstance(item, dict)
                    and isinstance(item.get("path"), str)
                    and Path(item["path"]).expanduser().exists()
                },
                key=lambda path: str(path),
            )
        except (OSError, json.JSONDecodeError):
            candidates = []
    if not candidates:
        candidates = sorted(
            path for path in scan_root.iterdir() if path.is_dir() or path.is_symlink()
        )
    for index, path in enumerate(candidates[:MAX_REF_REPOS]):
        resolved = path.resolve()
        git_dir = resolved / ".git"
        item = {
            "name": path.name,
            "path": str(path),
            "resolved_path": str(resolved),
            "is_symlink": path.is_symlink(),
            "git_repository": git_dir.exists(),
        }
        if git_dir.exists():
            head = run_command(["git", "rev-parse", "HEAD"], cwd=resolved, timeout=3)
            status = run_command(["git", "status", "--short"], cwd=resolved, timeout=3)
            item["head"] = head["stdout"].strip()
            item["dirty"] = bool(status["stdout"].strip())
        if index < MAX_REF_KNOWLEDGE_REPOS:
            readme = next(
                (
                    candidate
                    for candidate in (
                        resolved / "README.md",
                        resolved / "README",
                        resolved / "README.rst",
                    )
                    if candidate.is_file() and safe_document(candidate)
                ),
                None,
            )
            if readme is not None:
                raw = readme.read_bytes()
                excerpt = raw[:MAX_REF_KNOWLEDGE_BYTES]
                item["knowledge_document"] = {
                    "path": str(readme),
                    "content_sha256": hashlib.sha256(raw).hexdigest(),
                    "excerpt": redact(
                        excerpt.decode("utf-8", errors="replace")
                    ),
                    "excerpt_truncated": len(raw) > len(excerpt),
                }
        repositories.append(item)
    return {
        "available": True,
        "path": str(ref_root),
        "collection_root": str(scan_root),
        "repository_count": len(repositories),
        "truncated": len(candidates) > MAX_REF_REPOS,
        "repositories": repositories,
    }


def observe_test_command(
    workspace: Path,
    command: str,
    *,
    timeout: int,
) -> Dict[str, Any]:
    if not command.strip():
        return {"executed": False}
    args = shlex.split(command)
    if not args:
        raise ValueError("test command cannot be empty")
    result = run_command(args, cwd=workspace, timeout=timeout)
    return {
        "executed": True,
        "command": args,
        "returncode": result["returncode"],
        "passed": result["returncode"] == 0,
        "timed_out": result["timed_out"],
        "stdout_tail": result["stdout"][-12_000:],
        "stderr_tail": result["stderr"][-8_000:],
    }


def compare_snapshots(
    previous: Optional[Dict[str, Any]], current: Dict[str, Any]
) -> Dict[str, Any]:
    if not previous:
        reasons = ["initial_observation"]
        current_test = current.get("signals", {}).get("test", {})
        if current_test.get("executed") and not current_test.get("passed"):
            reasons.append("test_failed")
        return {
            "baseline_available": False,
            "changed": True,
            "reasons": reasons,
        }
    reasons = []
    previous_git = previous.get("signals", {}).get("git", {})
    current_git = current.get("signals", {}).get("git", {})
    if previous_git.get("head") != current_git.get("head"):
        reasons.append("git_head_changed")
    if previous_git.get("status") != current_git.get("status"):
        reasons.append("git_status_changed")
    previous_documents = {
        item["path"]: item["content_sha256"]
        for item in previous.get("signals", {}).get("documents", {}).get("documents", [])
    }
    current_documents = {
        item["path"]: item["content_sha256"]
        for item in current.get("signals", {}).get("documents", {}).get("documents", [])
    }
    if previous_documents != current_documents:
        reasons.append("document_set_or_content_changed")
    previous_plan = (
        previous.get("signals", {})
        .get("palamedes_state", {})
        .get("plan", {})
        .get("content_sha256")
    )
    current_plan = (
        current.get("signals", {})
        .get("palamedes_state", {})
        .get("plan", {})
        .get("content_sha256")
    )
    if previous_plan != current_plan:
        reasons.append("palamedes_plan_changed")
    previous_outcomes = (
        previous.get("signals", {})
        .get("palamedes_state", {})
        .get("outcomes", {})
        .get("content_sha256")
    )
    current_outcomes = (
        current.get("signals", {})
        .get("palamedes_state", {})
        .get("outcomes", {})
        .get("content_sha256")
    )
    if previous_outcomes != current_outcomes and current_outcomes:
        reasons.append("mission_outcome_appended")
    previous_ref = {
        item["name"]: item.get("head", "")
        for item in previous.get("signals", {}).get("reference_root", {}).get("repositories", [])
    }
    current_ref = {
        item["name"]: item.get("head", "")
        for item in current.get("signals", {}).get("reference_root", {}).get("repositories", [])
    }
    if previous_ref != current_ref:
        reasons.append("reference_repository_set_or_head_changed")
    current_test = current.get("signals", {}).get("test", {})
    if current_test.get("executed") and not current_test.get("passed"):
        reasons.append("test_failed")
    return {
        "baseline_available": True,
        "previous_observation_id": previous.get("observation_id", ""),
        "changed": bool(reasons),
        "reasons": reasons,
    }


def observation_context(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    documents = snapshot["signals"]["documents"]["documents"]
    return {
        "observation_id": snapshot["observation_id"],
        "observed_at": snapshot["observed_at"],
        "change": snapshot["change"],
        "git": snapshot["signals"]["git"],
        "documents": [
            {
                "path": item["path"],
                "content_sha256": item["content_sha256"],
                "headings": item["headings"],
                "excerpt": item["excerpt"][:8_000],
                "excerpt_truncated": item["excerpt_truncated"],
            }
            for item in documents
        ],
        "todos": snapshot["signals"]["todos"],
        "palamedes_state": snapshot["signals"]["palamedes_state"],
        "reference_root": snapshot["signals"]["reference_root"],
        "test": snapshot["signals"]["test"],
    }


def collect_observation(
    workspace: Path,
    *,
    state_root: Optional[Path] = None,
    ref_root: Optional[Path] = None,
    test_command: str = "",
    test_timeout: int = 120,
    persist: bool = True,
) -> Dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    if not workspace.is_dir():
        raise ValueError(f"workspace does not exist: {workspace}")
    state_root = state_root or workspace / ".palamedes" / "observations"
    latest_path = state_root / "latest.json"
    previous = None
    if latest_path.is_file():
        try:
            previous = json.loads(latest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None
    observed_at = utc_now()
    signals = {
        "documents": observe_documents(workspace),
        "git": observe_git(workspace),
        "todos": observe_todos(workspace),
        "palamedes_state": observe_palamedes_state(workspace),
        "reference_root": observe_ref_root(ref_root),
        "test": observe_test_command(
            workspace, test_command, timeout=max(1, min(test_timeout, 3600))
        ),
    }
    identity = {
        "workspace": str(workspace),
        "observed_at": observed_at,
        "signals_fingerprint": fingerprint(signals),
    }
    snapshot = {
        "observation_version": "palamedes-workspace-observation/1",
        "observation_id": f"observation-{fingerprint(identity)[:12]}",
        "observed_at": observed_at,
        "workspace": str(workspace),
        "signals": signals,
        "collection_limits": {
            "max_document_bytes": MAX_DOCUMENT_BYTES,
            "max_total_document_bytes": MAX_TOTAL_DOCUMENT_BYTES,
            "max_documents": MAX_DOCUMENTS,
            "max_todos": MAX_TODOS,
            "max_ref_repositories": MAX_REF_REPOS,
            "max_ref_knowledge_repositories": MAX_REF_KNOWLEDGE_REPOS,
            "max_ref_knowledge_bytes": MAX_REF_KNOWLEDGE_BYTES,
        },
        "secret_redaction_enabled": True,
    }
    snapshot["change"] = compare_snapshots(previous, snapshot)
    snapshot["snapshot_fingerprint"] = fingerprint(snapshot)
    if persist:
        state_root.mkdir(parents=True, exist_ok=True)
        archive = state_root / f"{snapshot['observation_id']}.json"
        encoded = json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        archive.write_text(encoded, encoding="utf-8")
        temporary = latest_path.with_suffix(".json.tmp")
        temporary.write_text(encoded, encoding="utf-8")
        temporary.replace(latest_path)
    return snapshot


def render_observation(snapshot: Dict[str, Any]) -> str:
    signals = snapshot["signals"]
    change = snapshot["change"]
    git = signals["git"]
    test = signals["test"]
    return "\n".join(
        [
            f"Observation: {snapshot['observation_id']}",
            f"  workspace: {snapshot['workspace']}",
            f"  changed: {change['changed']}",
            f"  reasons: {', '.join(change['reasons']) or 'none'}",
            f"  documents: {signals['documents']['document_count']}",
            f"  git head: {git.get('head', '') or 'unavailable'}",
            f"  dirty entries: {len(git.get('status', []))}",
            f"  TODO/FIXME: {len(signals['todos']['items'])}",
            f"  reference repos: {signals['reference_root'].get('repository_count', 0)}",
            (
                f"  test: {'PASS' if test.get('passed') else 'FAIL'}"
                if test.get("executed")
                else "  test: not executed"
            ),
        ]
    )


def bind_workspace(palamedes_module: Any, workspace: Path) -> None:
    palamedes_module.ROOT = workspace
    palamedes_module.STATE_DIR = workspace / ".palamedes"
    palamedes_module.PLAN_PATH = palamedes_module.STATE_DIR / "plan.json"
    palamedes_module.DECISIONS_PATH = palamedes_module.STATE_DIR / "decisions.jsonl"
    palamedes_module.RISKS_PATH = palamedes_module.STATE_DIR / "risks.jsonl"
    palamedes_module.EVENTS_PATH = palamedes_module.STATE_DIR / "events.jsonl"
    palamedes_module.REVISIONS_PATH = palamedes_module.STATE_DIR / "revisions.jsonl"


def cmd_observe(args: Any, palamedes_module: Any) -> None:
    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else Path.cwd().resolve()
    )
    bind_workspace(palamedes_module, workspace)
    ref_value = args.ref_root or os.environ.get("PALAMEDES_REF_ROOT", "")
    snapshot = collect_observation(
        workspace,
        ref_root=Path(ref_value).expanduser() if ref_value else None,
        test_command=args.test_command,
        test_timeout=args.test_timeout,
    )
    if args.json:
        print(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_observation(snapshot))
