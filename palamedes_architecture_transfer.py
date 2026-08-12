#!/usr/bin/env python3
"""Bounded, evidence-only transfer of architecture mechanisms across domains.

GitNexus is used here as a source locator, never as a design authority.  The
adapter binds every excerpt to a host-observed repository path and revision;
the transfer validator then permits only mappings that cite those source IDs
and a separate, caller-owned allow-list of target facts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence


EVIDENCE_PACKET_VERSION = "palamedes-gitnexus-evidence/1"
TRANSFER_CONTRACT_VERSION = "palamedes-architecture-transfer/1"
MECHANISM_QUERY_VERSION = "palamedes-mechanism-query/1"

AUTHORITY_FIELDS = (
    "decision_authority_granted",
    "design_authority_granted",
    "selection_authority_granted",
    "delivery_authority_granted",
    "code_reuse_authority_granted",
)
TRANSFER_DIFFERENCE_FIELDS = (
    "timing",
    "institution",
    "scale",
    "beneficiary_power",
    "authority_and_data",
)
PRESSURE_SEARCH_VOCABULARY = {
    "failure": (
        "failure", "retry", "recovery", "duplicate", "idempotent",
        "reconciliation", "compensating", "실패", "재시도", "복구", "중복",
    ),
    "consistency": (
        "consistency", "consistent", "ledger", "transaction", "checkpoint",
        "state machine", "invariant", "atomic", "versioning", "일관성", "원장",
        "트랜잭션", "체크포인트", "불변",
    ),
    "rollback": (
        "rollback", "roll back", "reversible", "migration", "replay",
        "compensation", "롤백", "되돌", "마이그레이션", "재생",
    ),
    "authority": (
        "authority", "permission", "entitlement", "ownership", "approval",
        "capability", "access control", "권한", "소유", "승인", "자격",
    ),
}
TOPIC_COPY_TERMS = (
    "battle pass", "battlepass", "season pass", "reward track",
    "배틀 패스", "배틀패스", "시즌 패스", "보상 트랙",
)
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _text(value: Any, field: str, *, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    result = value.strip()
    if len(result) > maximum:
        raise ValueError(f"{field} exceeds {maximum} characters")
    return result


def _exact_false(row: Mapping[str, Any], field: str) -> None:
    if field not in row or row[field] is not False:
        raise ValueError(f"{field} must be exactly false")


def _bounded_int(value: Any, field: str, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return value


def _strings(
    value: Any,
    field: str,
    *,
    minimum: int = 1,
    maximum: int = 20,
    item_maximum: int = 1000,
) -> List[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{field} must contain between {minimum} and {maximum} strings")
    result = [_text(item, f"{field}[]", maximum=item_maximum) for item in value]
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must contain unique strings")
    return result


def _safe_relative_path(value: Any, field: str = "file_path") -> str:
    text = _text(value, field, maximum=2000).replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"{field} must be a safe repository-relative path")
    return str(path)


def _canonical_absolute_path(value: Any, field: str) -> str:
    text = _text(value, field, maximum=4000)
    path = Path(text).expanduser()
    if not path.is_absolute():
        raise ValueError(f"{field} must be absolute")
    return str(path.resolve(strict=False))


@dataclass(frozen=True)
class EvidenceLimits:
    """Hard host-side bounds; callbacks cannot enlarge these limits."""

    max_repositories: int = 4
    max_queries: int = 3
    max_results_per_query: int = 6
    max_sources_total: int = 24
    max_excerpt_chars: int = 1600
    max_total_excerpt_chars: int = 24000
    max_query_chars: int = 480
    timeout_seconds: int = 30

    def validated(self) -> "EvidenceLimits":
        ceilings = {
            "max_repositories": (1, 16),
            "max_queries": (1, 8),
            "max_results_per_query": (1, 20),
            "max_sources_total": (1, 80),
            "max_excerpt_chars": (80, 4000),
            "max_total_excerpt_chars": (1000, 80000),
            "max_query_chars": (32, 1000),
            "timeout_seconds": (1, 60),
        }
        for field, bounds in ceilings.items():
            _bounded_int(getattr(self, field), field, minimum=bounds[0], maximum=bounds[1])
        if self.max_sources_total > self.max_repositories * self.max_queries * self.max_results_per_query:
            raise ValueError("max_sources_total exceeds the repository/query result envelope")
        return self


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str = ""


Runner = Callable[..., Any]


def _default_runner(args: Sequence[str], *, cwd: Path, timeout: int) -> CommandResult:
    completed = subprocess.run(
        list(args), cwd=str(cwd), capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    return CommandResult(completed.returncode, completed.stdout, completed.stderr)


def _normalize_result(value: Any) -> CommandResult:
    if isinstance(value, CommandResult):
        return value
    if isinstance(value, str):
        return CommandResult(0, value, "")
    if isinstance(value, Mapping):
        return CommandResult(
            int(value.get("returncode", 0)),
            str(value.get("stdout", "")),
            str(value.get("stderr", "")),
        )
    if isinstance(value, tuple) and 2 <= len(value) <= 3:
        return CommandResult(int(value[0]), str(value[1]), str(value[2]) if len(value) == 3 else "")
    if hasattr(value, "returncode") and hasattr(value, "stdout"):
        return CommandResult(
            int(value.returncode), str(value.stdout or ""), str(getattr(value, "stderr", "") or "")
        )
    raise TypeError("runner must return CommandResult, CompletedProcess, mapping, tuple, or string")


def _decode_json_output(output: str, field: str) -> Any:
    stripped = output.strip()
    if not stripped:
        raise ValueError(f"{field} returned empty output")
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        starts = [position for position in (stripped.find("{"), stripped.find("[")) if position >= 0]
        if starts:
            try:
                return json.loads(stripped[min(starts):])
            except json.JSONDecodeError:
                pass
    raise ValueError(f"{field} did not return JSON")


def _repo_snapshot_id(path: str, revision: str) -> str:
    return "gitnexus-repo:" + _sha256_text(f"{path}\0{revision}")


def _source_id(
    snapshot_id: str,
    native_symbol_id: str,
    excerpt_sha256: str,
    revision_file_sha256: str,
) -> str:
    digest = _sha256_text(
        f"{snapshot_id}\0{native_symbol_id}\0{excerpt_sha256}\0{revision_file_sha256}"
    )
    return f"gitnexus-source:{digest}"


def _packet_id(packet_without_id: Mapping[str, Any]) -> str:
    return "gitnexus-packet:" + _fingerprint(packet_without_id)


def _authority_false_fields() -> Dict[str, bool]:
    return {field: False for field in AUTHORITY_FIELDS}


def _query_categories(search_terms: Sequence[str]) -> set[str]:
    haystack = " ".join(search_terms).casefold()
    return {
        category for category, vocabulary in PRESSURE_SEARCH_VOCABULARY.items()
        if any(term.casefold() in haystack for term in vocabulary)
    }


def validate_mechanism_queries(
    rows: Any,
    *,
    target_fact_ids: Iterable[str],
    max_queries: int = 3,
    max_query_chars: int = 480,
) -> List[Dict[str, Any]]:
    _bounded_int(max_queries, "max_queries", minimum=1, maximum=8)
    allowed_target_ids = {_text(item, "target_fact_ids[]", maximum=300) for item in target_fact_ids}
    if not allowed_target_ids:
        raise ValueError("target_fact_ids cannot be empty")
    if not isinstance(rows, list) or not 1 <= len(rows) <= max_queries:
        raise ValueError(f"mechanism_queries must contain between 1 and {max_queries} rows")
    normalized: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    covered_categories: set[str] = set()
    for index, value in enumerate(rows):
        if not isinstance(value, Mapping):
            raise ValueError(f"mechanism_queries[{index}] must be an object")
        query_id = _text(value.get("query_id"), f"mechanism_queries[{index}].query_id", maximum=120)
        if query_id in seen_ids:
            raise ValueError("mechanism query IDs must be unique")
        seen_ids.add(query_id)
        mechanism = _text(value.get("mechanism"), f"{query_id}.mechanism", maximum=max_query_chars)
        target_pressure = _text(value.get("target_pressure"), f"{query_id}.target_pressure", maximum=max_query_chars)
        evidence_ids = _strings(
            value.get("target_evidence_ids"), f"{query_id}.target_evidence_ids",
            maximum=12, item_maximum=300,
        )
        unknown = sorted(set(evidence_ids) - allowed_target_ids)
        if unknown:
            raise ValueError(f"{query_id} cites unknown target fact IDs: {', '.join(unknown)}")
        search_terms = _strings(
            value.get("search_terms"), f"{query_id}.search_terms",
            minimum=2, maximum=8, item_maximum=120,
        )
        joined = " ".join(search_terms)
        if len(joined) > max_query_chars:
            raise ValueError(f"{query_id}.search_terms exceed query length bound")
        if any(term in joined.casefold() for term in TOPIC_COPY_TERMS):
            raise ValueError(f"{query_id} searches a feature/topic name instead of mechanisms")
        categories = _query_categories(search_terms)
        if not categories:
            raise ValueError(
                f"{query_id}.search_terms must address failure, consistency, rollback, or authority"
            )
        covered_categories.update(categories)
        normalized.append({
            "query_id": query_id,
            "mechanism": mechanism,
            "target_pressure": target_pressure,
            "target_evidence_ids": evidence_ids,
            "search_terms": search_terms,
        })
    missing_categories = sorted(set(PRESSURE_SEARCH_VOCABULARY) - covered_categories)
    if missing_categories:
        raise ValueError(
            "mechanism query portfolio must explicitly cover: " + ", ".join(missing_categories)
        )
    return normalized


def _target_facts(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError("target_facts must be a non-empty list")
    result: List[Dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ValueError(f"target_facts[{index}] must be an object")
        fact_id = _text(row.get("fact_id"), f"target_facts[{index}].fact_id", maximum=300)
        fact = _text(row.get("fact"), f"target_facts[{index}].fact", maximum=2000)
        if fact_id in seen:
            raise ValueError("target fact IDs must be unique")
        seen.add(fact_id)
        result.append({"fact_id": fact_id, "fact": fact})
    return result


def propose_mechanism_queries(
    ask: Callable[[str, str], Any],
    target_facts: Any,
    *,
    max_queries: int = 3,
) -> List[Dict[str, Any]]:
    """Ask for causal/mechanism searches without leaking a proposed feature name."""

    facts = _target_facts(target_facts)
    ids = [row["fact_id"] for row in facts]
    prompt = f"""
Derive at most {max_queries} cross-domain architecture searches from the trusted
target facts below. Search by operational pressure and causal mechanism, never by
the target product/feature name. Across the portfolio explicitly cover failure and
recovery, consistency and invariants, rollback/reversibility, and authority or
entitlement boundaries. Return JSON with `mechanism_queries`; every row must have
exactly query_id, mechanism, target_pressure, target_evidence_ids, search_terms.
Only cite supplied fact IDs. Search terms are literal GitNexus terms, not claims.

Target facts: {_canonical_json(facts)}
"""
    last_error = ""
    for attempt in range(2):
        repair = "" if attempt == 0 else f"\nPrevious output was invalid: {last_error}. Return one corrected JSON object."
        raw = ask("architecture_transfer_mechanism_query_designer", prompt + repair)
        rows = raw.get("mechanism_queries") if isinstance(raw, Mapping) else raw
        try:
            return validate_mechanism_queries(rows, target_fact_ids=ids, max_queries=max_queries)
        except ValueError as exc:
            last_error = str(exc)
    raise ValueError(f"mechanism query provider failed contract after repair: {last_error}")


class GitNexusEvidenceAdapter:
    """Collect revision-pinned excerpts from other indexed repositories.

    ``runner`` is injected at the process boundary and receives
    ``runner(args, cwd=Path(...), timeout=int)``.  Failures are data and are
    isolated per repository/query; no reference can grant any authority.
    """

    def __init__(
        self,
        runner: Optional[Runner] = None,
        *,
        cli_prefix: Optional[Sequence[str]] = None,
        limits: Optional[EvidenceLimits] = None,
    ) -> None:
        self.runner = runner or _default_runner
        self.cli_prefix = tuple(cli_prefix) if cli_prefix is not None else None
        self.limits = (limits or EvidenceLimits()).validated()

    def _prefix(self, current_repo: Path) -> List[str]:
        if self.cli_prefix:
            return list(self.cli_prefix)
        local = current_repo / ".gitnexus" / "run.cjs"
        if local.is_file():
            return ["node", str(local)]
        return ["gitnexus"]

    def _run(self, args: Sequence[str], *, cwd: Path) -> CommandResult:
        value = self.runner(list(args), cwd=cwd, timeout=self.limits.timeout_seconds)
        result = _normalize_result(value)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip().splitlines()
            message = detail[-1][:300] if detail else f"exit {result.returncode}"
            raise RuntimeError(message)
        return result

    def _list_repositories(self, *, current_repo: Path) -> List[Dict[str, str]]:
        result = self._run([*self._prefix(current_repo), "list"], cwd=current_repo)
        output = result.stdout.strip()
        try:
            decoded = _decode_json_output(output, "gitnexus list")
        except ValueError:
            return self._parse_human_list(output)
        values = decoded.get("repositories") if isinstance(decoded, Mapping) else decoded
        if not isinstance(values, list):
            raise ValueError("gitnexus list repositories must be an array")
        rows: List[Dict[str, str]] = []
        for index, raw in enumerate(values):
            if not isinstance(raw, Mapping):
                raise ValueError(f"repository catalog row {index} is not an object")
            rows.append({
                "repository": _text(raw.get("name") or raw.get("repository"), "repository.name", maximum=300),
                "repository_path": _canonical_absolute_path(raw.get("path") or raw.get("repository_path"), "repository.path"),
                "listed_revision": _text(
                    raw.get("lastCommit") or raw.get("revision") or raw.get("commit"),
                    "repository.revision", maximum=80,
                ).casefold(),
            })
        return rows

    @staticmethod
    def _parse_human_list(output: str) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        current: Dict[str, str] = {}
        for line in output.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Indexed Repositories"):
                continue
            match = re.match(r"^(Path|Commit):\s*(.+)$", stripped)
            if match:
                key = "repository_path" if match.group(1) == "Path" else "listed_revision"
                current[key] = match.group(2).strip()
                if {"repository", "repository_path", "listed_revision"}.issubset(current):
                    rows.append({
                        "repository": current["repository"],
                        "repository_path": _canonical_absolute_path(current["repository_path"], "repository.path"),
                        "listed_revision": current["listed_revision"].casefold(),
                    })
                    current = {}
                continue
            indent = len(line) - len(line.lstrip())
            # Current CLI renders repository headings with two spaces and their
            # attributes with four.  Also accept an unindented heading for older
            # versions, but never mistake a labelled attribute for a name.
            if indent in (0, 2) and ":" not in stripped and not stripped.startswith("Repository"):
                current = {"repository": _text(stripped, "repository.name", maximum=300)}
        if not rows:
            raise ValueError("unable to parse gitnexus list output")
        return rows

    def _git_snapshot(self, repo: Mapping[str, str], *, current_repo: Path) -> Dict[str, str]:
        path = Path(repo["repository_path"])
        head = self._run(["git", "-C", str(path), "rev-parse", "HEAD"], cwd=current_repo).stdout.strip().casefold()
        if not _SHA40.fullmatch(head):
            raise ValueError("git HEAD is not a full 40-hex revision")
        listed = repo["listed_revision"]
        if not re.fullmatch(r"[0-9a-f]{7,40}", listed) or not head.startswith(listed):
            raise ValueError("GitNexus indexed revision differs from repository HEAD")
        metadata_revision = ""
        for filename in ("gitnexus.json", "meta.json"):
            metadata = path / ".gitnexus" / filename
            try:
                decoded = json.loads(metadata.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            candidate = str(decoded.get("lastCommit", "")).strip().casefold()
            if candidate:
                metadata_revision = candidate
                break
        if metadata_revision and metadata_revision != head:
            raise ValueError("GitNexus metadata revision differs from repository HEAD")
        status = self._run(
            ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=all"],
            cwd=current_repo,
        ).stdout.strip()
        canonical_path = str(path.resolve(strict=False))
        return {
            "repository": repo["repository"],
            "repository_path": canonical_path,
            "revision": head,
            "repo_snapshot_id": _repo_snapshot_id(canonical_path, head),
            # Query evidence comes from the revision-pinned GitNexus index, not
            # the live worktree. Preserve a status fingerprint so a moving dirty
            # tree is detected across the collection window; each cited excerpt
            # is independently checked against `git show <revision>:<path>`.
            "worktree_dirty": bool(status),
            "worktree_status_fingerprint": _sha256_text(status),
        }

    def _query(self, repo: Mapping[str, str], query: Mapping[str, Any], *, current_repo: Path) -> Any:
        search = " ".join(query["search_terms"])
        return _decode_json_output(
            self._run([
                *self._prefix(current_repo), "query", "--repo", repo["repository"],
                # GitNexus content output can exceed its CLI JSON buffer and
                # become an invalid truncated document. Query only identities
                # and source ranges; read the actual excerpt from the pinned git
                # revision below.
                "--limit", str(self.limits.max_results_per_query),
                "--query", search,
            ], cwd=current_repo).stdout,
            "gitnexus query",
        )

    def _extract_sources(
        self,
        decoded: Any,
        *,
        repo: Mapping[str, str],
        query_id: str,
        current_repo: Path,
    ) -> List[Dict[str, Any]]:
        if not isinstance(decoded, Mapping):
            raise ValueError("GitNexus query result must be an object")
        if decoded.get("error"):
            raise ValueError("GitNexus query returned an error")
        if decoded.get("partial") is True or decoded.get("truncated") is True:
            raise ValueError("GitNexus query returned partial evidence")
        candidates: List[tuple[str, Any]] = []
        for key, kind in (("process_symbols", "process_symbol"), ("definitions", "definition")):
            values = decoded.get(key, [])
            if not isinstance(values, list):
                raise ValueError(f"GitNexus query {key} must be an array")
            candidates.extend((kind, value) for value in values)
        normalized: List[Dict[str, Any]] = []
        committed_files: Dict[str, str] = {}
        for kind, value in candidates:
            if not isinstance(value, Mapping):
                continue
            native_id = value.get("id") or value.get("uid")
            file_path = value.get("filePath") or value.get("file_path")
            symbol = value.get("name") or value.get("symbol")
            if not all(
                isinstance(item, str) and item.strip()
                for item in (native_id, file_path, symbol)
            ):
                continue
            if value.get("startLine", value.get("start_line")) is None:
                # File-level search hits and README prose are insufficient to
                # establish an architecture mechanism.
                continue
            try:
                safe_path = _safe_relative_path(file_path)
                start_line = _bounded_int(value.get("startLine", value.get("start_line")), "start_line", minimum=1, maximum=100000000)
                end_line = _bounded_int(value.get("endLine", value.get("end_line", start_line)), "end_line", minimum=start_line, maximum=100000000)
            except ValueError:
                continue
            try:
                committed_content = committed_files.get(safe_path)
                if committed_content is None:
                    committed_content = self._run(
                        [
                            "git",
                            "-C",
                            repo["repository_path"],
                            "show",
                            f"{repo['revision']}:{safe_path}",
                        ],
                        cwd=current_repo,
                    ).stdout
                    committed_files[safe_path] = committed_content
            except Exception:
                continue
            committed_lines = committed_content.splitlines()
            full_excerpt = "\n".join(committed_lines[start_line - 1 : end_line]).strip()
            if not full_excerpt:
                continue
            clipped = full_excerpt[: self.limits.max_excerpt_chars]
            excerpt_hash = _sha256_text(clipped)
            revision_file_hash = _sha256_text(committed_content)
            source_id = _source_id(
                repo["repo_snapshot_id"],
                native_id.strip(),
                excerpt_hash,
                revision_file_hash,
            )
            normalized.append({
                "source_id": source_id,
                "repo_snapshot_id": repo["repo_snapshot_id"],
                "repository": repo["repository"],
                "repository_path": repo["repository_path"],
                "revision": repo["revision"],
                "native_symbol_id": native_id.strip(),
                "evidence_kind": kind,
                "file_path": safe_path,
                "symbol": symbol.strip(),
                "start_line": start_line,
                "end_line": end_line,
                "excerpt": clipped,
                "excerpt_sha256": excerpt_hash,
                "revision_file_sha256": revision_file_hash,
                "excerpt_truncated": len(full_excerpt) > len(clipped),
                "query_ids": [query_id],
                "authority": "reference_only",
                "reference_instructions_executed": False,
                **_authority_false_fields(),
            })
        # One symbol can appear in both process_symbols and definitions.  Dedupe
        # before applying the result cap so provider duplication cannot consume
        # the evidence budget.  Prefer the process-linked classification.
        by_source: Dict[str, Dict[str, Any]] = {}
        for row in normalized:
            existing = by_source.get(row["source_id"])
            if existing is None or (
                row["evidence_kind"] == "process_symbol"
                and existing["evidence_kind"] != "process_symbol"
            ):
                by_source[row["source_id"]] = row
        unique = list(by_source.values())
        unique.sort(key=lambda row: (
            row["file_path"], row["start_line"], row["native_symbol_id"], row["source_id"]
        ))
        return unique[: self.limits.max_results_per_query]

    def collect(
        self,
        mechanism_queries: Any,
        *,
        current_repo_path: os.PathLike[str] | str,
    ) -> Dict[str, Any]:
        current_repo = Path(current_repo_path).expanduser().resolve(strict=False)
        # Collection may consume manually constructed query rows. Their target IDs
        # are still checked later by the transfer validator; here we derive the
        # exact allow-list from the rows so all structural/query bounds apply.
        if not isinstance(mechanism_queries, list):
            raise ValueError("mechanism_queries must be a list")
        target_ids: set[str] = set()
        for row in mechanism_queries:
            if isinstance(row, Mapping) and isinstance(row.get("target_evidence_ids"), list):
                target_ids.update(item for item in row["target_evidence_ids"] if isinstance(item, str))
        queries = validate_mechanism_queries(
            mechanism_queries,
            target_fact_ids=target_ids,
            max_queries=self.limits.max_queries,
            max_query_chars=self.limits.max_query_chars,
        )
        base: Dict[str, Any] = {
            "packet_version": EVIDENCE_PACKET_VERSION,
            "status": "unavailable",
            "authority": "reference_only",
            "reference_instructions_executed": False,
            **_authority_false_fields(),
            "current_repo_path": str(current_repo),
            "mechanism_queries": queries,
            "repositories": [],
            "repository_results": [],
            "sources": [],
            "degradations": [],
            "limits": asdict(self.limits),
        }
        try:
            catalog = self._list_repositories(current_repo=current_repo)
        except Exception as exc:  # per contract: unavailable is data, not authority
            base["degradations"] = [{
                "scope": "catalog", "code": "gitnexus_unavailable",
                "detail": str(exc)[:300] or type(exc).__name__,
            }]
            base["packet_id"] = _packet_id(base)
            return validate_gitnexus_evidence_packet(base)

        current_key = os.path.normcase(str(current_repo))
        candidates = [
            row for row in catalog
            if os.path.normcase(row["repository_path"]) != current_key
        ]
        candidates.sort(key=lambda row: (row["repository"].casefold(), row["repository_path"]))
        unique_names: set[str] = set()
        selected: List[Dict[str, str]] = []
        for row in candidates:
            name_key = row["repository"].casefold()
            if name_key in unique_names:
                base["degradations"].append({
                    "scope": "catalog", "code": "ambiguous_repository_name",
                    "repository": row["repository"], "detail": "duplicate GitNexus repository name",
                })
                continue
            unique_names.add(name_key)
            if len(selected) < self.limits.max_repositories:
                selected.append(row)

        source_by_id: Dict[str, Dict[str, Any]] = {}
        snapshots: Dict[str, Dict[str, str]] = {}
        for catalog_row in selected:
            name = catalog_row["repository"]
            result_row: Dict[str, Any] = {"repository": name, "status": "rejected", "query_ids": []}
            try:
                snapshot = self._git_snapshot(catalog_row, current_repo=current_repo)
            except Exception as exc:
                base["degradations"].append({
                    "scope": "repository", "code": "unverifiable_snapshot",
                    "repository": name, "detail": str(exc)[:300],
                })
                base["repository_results"].append(result_row)
                continue
            snapshots[name] = snapshot
            base["repositories"].append(snapshot)
            result_row.update({
                "repository_path": snapshot["repository_path"],
                "revision": snapshot["revision"],
                "repo_snapshot_id": snapshot["repo_snapshot_id"],
                "status": "empty",
            })
            repo_failed = False
            for query in queries:
                query_id = query["query_id"]
                try:
                    decoded = self._query(snapshot, query, current_repo=current_repo)
                    rows = self._extract_sources(
                        decoded,
                        repo=snapshot,
                        query_id=query_id,
                        current_repo=current_repo,
                    )
                except Exception as exc:
                    repo_failed = True
                    base["degradations"].append({
                        "scope": "query", "code": "query_failed", "repository": name,
                        "query_id": query_id, "detail": str(exc)[:300],
                    })
                    continue
                result_row["query_ids"].append(query_id)
                if rows:
                    result_row["status"] = "ok"
                for row in rows:
                    existing = source_by_id.get(row["source_id"])
                    if existing is None:
                        source_by_id[row["source_id"]] = row
                    else:
                        existing["query_ids"] = sorted(set(existing["query_ids"] + row["query_ids"]))
            if repo_failed:
                result_row["status"] = "degraded"
            result_row["query_ids"] = sorted(set(result_row["query_ids"]))
            base["repository_results"].append(result_row)

        # Re-check both Git state and the GitNexus catalog after reading.  A
        # moving snapshot invalidates only that repository's evidence.
        drifted: set[str] = set()
        try:
            final_catalog = self._list_repositories(current_repo=current_repo)
            final_by_path = {row["repository_path"]: row for row in final_catalog}
            for name, snapshot in snapshots.items():
                final_row = final_by_path.get(snapshot["repository_path"])
                if final_row is None:
                    raise ValueError(f"repository disappeared from catalog: {name}")
                final_snapshot = self._git_snapshot(final_row, current_repo=current_repo)
                if final_snapshot != snapshot:
                    drifted.add(name)
        except Exception as exc:
            drifted.update(snapshots)
            base["degradations"].append({
                "scope": "catalog", "code": "post_collection_snapshot_unverifiable",
                "detail": str(exc)[:300],
            })
        if drifted:
            for name in sorted(drifted, key=str.casefold):
                base["degradations"].append({
                    "scope": "repository", "code": "snapshot_drift", "repository": name,
                    "detail": "repository or index changed during collection",
                })
            source_by_id = {
                source_id: row for source_id, row in source_by_id.items()
                if row["repository"] not in drifted
            }
            base["repositories"] = [row for row in base["repositories"] if row["repository"] not in drifted]
            for row in base["repository_results"]:
                if row["repository"] in drifted:
                    row["status"] = "degraded"

        sources = sorted(source_by_id.values(), key=lambda row: (
            row["repository"].casefold(), row["file_path"], row["start_line"],
            row["native_symbol_id"], row["source_id"],
        ))
        bounded_sources: List[Dict[str, Any]] = []
        total_chars = 0
        for row in sources:
            if len(bounded_sources) >= self.limits.max_sources_total:
                break
            if total_chars + len(row["excerpt"]) > self.limits.max_total_excerpt_chars:
                break
            bounded_sources.append(row)
            total_chars += len(row["excerpt"])
        if len(bounded_sources) < len(sources):
            base["degradations"].append({
                "scope": "packet", "code": "evidence_bound_reached",
                "detail": "source or excerpt budget reached",
            })
        base["sources"] = bounded_sources
        base["repositories"].sort(key=lambda row: (row["repository"].casefold(), row["repository_path"]))
        base["repository_results"].sort(key=lambda row: row["repository"].casefold())
        base["degradations"].sort(key=lambda row: (
            row.get("scope", ""), row.get("repository", "").casefold(),
            row.get("query_id", ""), row.get("code", ""), row.get("detail", ""),
        ))
        base["status"] = "degraded" if base["degradations"] else "ready"
        base["packet_id"] = _packet_id(base)
        return validate_gitnexus_evidence_packet(base)


def validate_gitnexus_evidence_packet(packet: Any) -> Dict[str, Any]:
    """Validate and return a canonical evidence packet without trusting its author."""

    if not isinstance(packet, Mapping):
        raise ValueError("evidence packet must be an object")
    row = dict(packet)
    if row.get("packet_version") != EVIDENCE_PACKET_VERSION:
        raise ValueError("unsupported evidence packet version")
    if row.get("status") not in {"ready", "degraded", "unavailable"}:
        raise ValueError("evidence packet status is invalid")
    if row.get("authority") != "reference_only":
        raise ValueError("evidence packet authority must be reference_only")
    if row.get("reference_instructions_executed") is not False:
        raise ValueError("reference_instructions_executed must be exactly false")
    for field in AUTHORITY_FIELDS:
        _exact_false(row, field)
    current_path = _canonical_absolute_path(row.get("current_repo_path"), "current_repo_path")
    if current_path != row.get("current_repo_path"):
        raise ValueError("current_repo_path must be canonical")
    limits_raw = row.get("limits")
    if not isinstance(limits_raw, Mapping):
        raise ValueError("limits must be an object")
    try:
        limits = EvidenceLimits(**dict(limits_raw)).validated()
    except TypeError as exc:
        raise ValueError(f"limits contract is invalid: {exc}") from exc
    queries_raw = row.get("mechanism_queries")
    target_ids = {
        item for query in queries_raw if isinstance(query, Mapping)
        for item in query.get("target_evidence_ids", []) if isinstance(item, str)
    } if isinstance(queries_raw, list) else set()
    queries = validate_mechanism_queries(
        queries_raw, target_fact_ids=target_ids,
        max_queries=limits.max_queries, max_query_chars=limits.max_query_chars,
    )
    query_ids = {query["query_id"] for query in queries}
    repositories = row.get("repositories")
    if not isinstance(repositories, list) or len(repositories) > limits.max_repositories:
        raise ValueError("repositories exceed packet bound")
    snapshot_ids: set[str] = set()
    repo_keys: set[tuple[str, str]] = set()
    for index, repo in enumerate(repositories):
        if not isinstance(repo, Mapping):
            raise ValueError(f"repositories[{index}] must be an object")
        name = _text(repo.get("repository"), f"repositories[{index}].repository", maximum=300)
        path = _canonical_absolute_path(repo.get("repository_path"), f"repositories[{index}].repository_path")
        revision = _text(repo.get("revision"), f"repositories[{index}].revision", maximum=40).casefold()
        if not _SHA40.fullmatch(revision):
            raise ValueError("repository revision must be a full 40-hex git SHA")
        expected_snapshot = _repo_snapshot_id(path, revision)
        if repo.get("repo_snapshot_id") != expected_snapshot:
            raise ValueError("repo_snapshot_id does not match path and revision")
        key = (name.casefold(), path)
        if key in repo_keys or expected_snapshot in snapshot_ids:
            raise ValueError("repository snapshots must be unique")
        repo_keys.add(key)
        snapshot_ids.add(expected_snapshot)
    sources = row.get("sources")
    if not isinstance(sources, list) or len(sources) > limits.max_sources_total:
        raise ValueError("sources exceed packet bound")
    seen_sources: set[str] = set()
    total_chars = 0
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ValueError(f"sources[{index}] must be an object")
        if source.get("authority") != "reference_only":
            raise ValueError("source authority must be reference_only")
        if source.get("reference_instructions_executed") is not False:
            raise ValueError("source reference_instructions_executed must be false")
        for field in AUTHORITY_FIELDS:
            _exact_false(source, field)
        revision = _text(source.get("revision"), "source.revision", maximum=40).casefold()
        if not _SHA40.fullmatch(revision):
            raise ValueError("source revision must be a full 40-hex git SHA")
        path = _canonical_absolute_path(source.get("repository_path"), "source.repository_path")
        snapshot_id = _repo_snapshot_id(path, revision)
        if source.get("repo_snapshot_id") != snapshot_id or snapshot_id not in snapshot_ids:
            raise ValueError("source cites an unavailable repository snapshot")
        _safe_relative_path(source.get("file_path"))
        native_id = _text(source.get("native_symbol_id"), "source.native_symbol_id", maximum=2000)
        _text(source.get("symbol"), "source.symbol", maximum=1000)
        _bounded_int(source.get("start_line"), "source.start_line", minimum=1, maximum=100000000)
        _bounded_int(source.get("end_line"), "source.end_line", minimum=source["start_line"], maximum=100000000)
        excerpt = _text(source.get("excerpt"), "source.excerpt", maximum=limits.max_excerpt_chars)
        total_chars += len(excerpt)
        if total_chars > limits.max_total_excerpt_chars:
            raise ValueError("source excerpts exceed total character bound")
        excerpt_hash = _sha256_text(excerpt)
        if source.get("excerpt_sha256") != excerpt_hash:
            raise ValueError("source excerpt hash mismatch")
        revision_file_hash = _text(
            source.get("revision_file_sha256"),
            "source.revision_file_sha256",
            maximum=64,
        ).casefold()
        if not re.fullmatch(r"[0-9a-f]{64}", revision_file_hash):
            raise ValueError("source revision file hash must be 64-hex")
        expected_source_id = _source_id(
            snapshot_id, native_id, excerpt_hash, revision_file_hash
        )
        if source.get("source_id") != expected_source_id:
            raise ValueError("source_id is not bound to snapshot, symbol, and excerpt")
        if expected_source_id in seen_sources:
            raise ValueError("source IDs must be unique")
        seen_sources.add(expected_source_id)
        cited_queries = _strings(source.get("query_ids"), "source.query_ids", maximum=limits.max_queries, item_maximum=120)
        if not set(cited_queries).issubset(query_ids):
            raise ValueError("source cites an unknown mechanism query")
        if source.get("evidence_kind") not in {"definition", "process_symbol"}:
            raise ValueError("source evidence_kind is invalid")
        if not isinstance(source.get("excerpt_truncated"), bool):
            raise ValueError("source excerpt_truncated must be boolean")
    results = row.get("repository_results")
    if not isinstance(results, list) or len(results) > limits.max_repositories:
        raise ValueError("repository_results exceed packet bound")
    degradations = row.get("degradations")
    if not isinstance(degradations, list):
        raise ValueError("degradations must be an array")
    if row["status"] == "ready" and degradations:
        raise ValueError("ready packet cannot contain degradations")
    if row["status"] == "unavailable" and (repositories or sources):
        raise ValueError("unavailable packet cannot contain repository evidence")
    packet_without_id = dict(row)
    supplied_id = packet_without_id.pop("packet_id", None)
    expected_id = _packet_id(packet_without_id)
    if supplied_id != expected_id:
        raise ValueError("packet_id does not match packet contents")
    # Return a detached canonical representation; timing/priority never entered it.
    return json.loads(_canonical_json(row))


def _mapping_rows(value: Any) -> Any:
    return value.get("transfers") if isinstance(value, Mapping) else value


def _normalized_words(value: str) -> set[str]:
    return {token for token in re.findall(r"[0-9a-zA-Z가-힣]+", value.casefold()) if len(token) > 2}


def validate_architecture_transfers(
    payload: Any,
    *,
    evidence_packet: Any,
    target_fact_ids: Iterable[str],
    max_transfers: int = 8,
    target_domain: str = "",
) -> List[Dict[str, Any]]:
    """Validate causal cross-domain mappings against two disjoint allow-lists."""

    packet = validate_gitnexus_evidence_packet(evidence_packet)
    _bounded_int(max_transfers, "max_transfers", minimum=1, maximum=20)
    source_catalog = {row["source_id"]: row for row in packet["sources"]}
    allowed_targets = {_text(item, "target_fact_ids[]", maximum=300) for item in target_fact_ids}
    if not allowed_targets:
        raise ValueError("target_fact_ids cannot be empty")
    rows = _mapping_rows(payload)
    if not isinstance(rows, list) or not 1 <= len(rows) <= max_transfers:
        raise ValueError(f"transfers must contain between 1 and {max_transfers} rows")
    expected_target_domain = target_domain.strip()
    result: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise ValueError(f"transfers[{index}] must be an object")
        transfer_id = _text(raw.get("transfer_id"), f"transfers[{index}].transfer_id", maximum=160)
        if transfer_id in seen_ids:
            raise ValueError("transfer IDs must be unique")
        seen_ids.add(transfer_id)
        source_ids = _strings(raw.get("source_ids"), f"{transfer_id}.source_ids", minimum=2, maximum=12, item_maximum=200)
        fabricated = sorted(set(source_ids) - set(source_catalog))
        if fabricated:
            raise ValueError(f"{transfer_id} cites unavailable source IDs: {', '.join(fabricated)}")
        source_domain = _text(raw.get("source_domain"), f"{transfer_id}.source_domain", maximum=200)
        row_target_domain = _text(raw.get("target_domain"), f"{transfer_id}.target_domain", maximum=200)
        if expected_target_domain and row_target_domain.casefold() != expected_target_domain.casefold():
            raise ValueError(f"{transfer_id}.target_domain does not match the trusted target domain")
        if source_domain.casefold() == row_target_domain.casefold():
            raise ValueError(f"{transfer_id} is same-domain topic copying")
        if raw.get("same_primary_job") is not False:
            raise ValueError(f"{transfer_id}.same_primary_job must be exactly false")
        if raw.get("source_outcome_is_target_forecast") is not False:
            raise ValueError(f"{transfer_id}.source_outcome_is_target_forecast must be exactly false")
        for field in AUTHORITY_FIELDS:
            _exact_false(raw, f"{transfer_id}.{field}" if False else field)
        source_pressure = _text(raw.get("source_pressure"), f"{transfer_id}.source_pressure")
        source_pattern = _text(raw.get("source_pattern"), f"{transfer_id}.source_pattern")
        source_invariant = _text(raw.get("source_invariant"), f"{transfer_id}.source_invariant")
        causal_chain = _strings(raw.get("source_causal_chain"), f"{transfer_id}.source_causal_chain", minimum=2, maximum=12)
        failure_prevented = _text(raw.get("failure_prevented"), f"{transfer_id}.failure_prevented")
        target_pressure = _text(raw.get("target_pressure"), f"{transfer_id}.target_pressure")
        if source_pressure.casefold() == target_pressure.casefold():
            raise ValueError(f"{transfer_id} copied source pressure without localizing the target pressure")
        target_evidence_ids = _strings(raw.get("target_evidence_ids"), f"{transfer_id}.target_evidence_ids", maximum=12, item_maximum=300)
        unavailable_targets = sorted(set(target_evidence_ids) - allowed_targets)
        if unavailable_targets:
            raise ValueError(f"{transfer_id} cites unavailable target evidence: {', '.join(unavailable_targets)}")
        if set(target_evidence_ids) & set(source_ids):
            raise ValueError(f"{transfer_id} mixes source and target evidence namespaces")
        adaptation = _text(raw.get("adaptation"), f"{transfer_id}.adaptation")
        if adaptation.casefold() == source_pattern.casefold():
            raise ValueError(f"{transfer_id} copies a source pattern without adaptation")
        target_tokens = _normalized_words(row_target_domain)
        source_side = " ".join((source_pressure, source_pattern, source_invariant)).casefold()
        if any(token in _normalized_words(source_side) for token in target_tokens):
            raise ValueError(f"{transfer_id} source mechanism contains target-domain topic terms")
        if any(term in source_side for term in TOPIC_COPY_TERMS):
            raise ValueError(f"{transfer_id} uses a target feature name as source architecture evidence")
        responsibility = raw.get("responsibility_mapping")
        if not isinstance(responsibility, list) or not responsibility:
            raise ValueError(f"{transfer_id}.responsibility_mapping must be non-empty")
        normalized_responsibility: List[Dict[str, str]] = []
        for map_index, mapping in enumerate(responsibility):
            if not isinstance(mapping, Mapping):
                raise ValueError(f"{transfer_id}.responsibility_mapping[{map_index}] must be an object")
            normalized_responsibility.append({
                "source_role": _text(mapping.get("source_role"), "source_role"),
                "target_role": _text(mapping.get("target_role"), "target_role"),
                "uncertainty": _text(mapping.get("uncertainty"), "uncertainty"),
            })
        differences = raw.get("material_differences")
        if not isinstance(differences, Mapping):
            raise ValueError(f"{transfer_id}.material_differences must be an object")
        normalized_differences = {
            field: _text(differences.get(field), f"{transfer_id}.material_differences.{field}")
            for field in TRANSFER_DIFFERENCE_FIELDS
        }
        non_transferable = _strings(
            raw.get("non_transferable_assumptions"), f"{transfer_id}.non_transferable_assumptions",
            maximum=12,
        )
        transfer_limit = _text(raw.get("transfer_limit"), f"{transfer_id}.transfer_limit")
        disconfirming = _strings(raw.get("disconfirming_evidence"), f"{transfer_id}.disconfirming_evidence", maximum=12)
        local_probe = _text(raw.get("local_probe"), f"{transfer_id}.local_probe")
        local_falsifier = _text(raw.get("local_falsifier"), f"{transfer_id}.local_falsifier")
        result.append({
            "transfer_id": transfer_id,
            "source_ids": source_ids,
            "source_revisions": sorted({source_catalog[item]["revision"] for item in source_ids}),
            "source_snapshot_ids": sorted({source_catalog[item]["repo_snapshot_id"] for item in source_ids}),
            "source_domain": source_domain,
            "target_domain": row_target_domain,
            "same_primary_job": False,
            "source_pressure": source_pressure,
            "source_pattern": source_pattern,
            "source_invariant": source_invariant,
            "source_causal_chain": causal_chain,
            "failure_prevented": failure_prevented,
            "target_pressure": target_pressure,
            "target_evidence_ids": target_evidence_ids,
            "responsibility_mapping": normalized_responsibility,
            "adaptation": adaptation,
            "material_differences": normalized_differences,
            "non_transferable_assumptions": non_transferable,
            "transfer_limit": transfer_limit,
            "disconfirming_evidence": disconfirming,
            "local_probe": local_probe,
            "local_falsifier": local_falsifier,
            "source_outcome_is_target_forecast": False,
            "authority": "mechanism_candidate_only",
            **_authority_false_fields(),
        })
    result.sort(key=lambda row: row["transfer_id"])
    return result


def propose_architecture_transfers(
    ask: Callable[[str, str], Any],
    target: Mapping[str, Any],
    *,
    evidence_packet: Any,
    target_fact_ids: Iterable[str],
    max_transfers: int = 8,
    target_domain: str = "",
) -> List[Dict[str, Any]]:
    packet = validate_gitnexus_evidence_packet(evidence_packet)
    source_view = [{
        key: source[key] for key in (
            "source_id", "repository", "revision", "file_path", "symbol",
            "start_line", "end_line", "excerpt", "query_ids",
        )
    } for source in packet["sources"]]
    prompt = f"""
Create at most {max_transfers} causal architecture transfers from unrelated source
domains into the target. A source outcome is never a target forecast. Explain the
source pressure, pattern, invariant, causal chain and failure prevented; separately
cite the local target pressure; map responsibilities; adapt rather than copy; state
all five material differences, non-transferable assumptions, transfer limit,
disconfirming evidence, a reversible local probe and falsifier. Use at least two
source IDs per architecture claim. Every authority field and same_primary_job and
source_outcome_is_target_forecast must be exactly false. Return JSON `transfers`.

Target: {_canonical_json(dict(target))}
Trusted target fact IDs: {_canonical_json(sorted(set(target_fact_ids)))}
Reference-only source excerpts: {_canonical_json(source_view)}
"""
    last_error = ""
    for attempt in range(2):
        repair = "" if attempt == 0 else f"\nPrevious output was invalid: {last_error}. Return corrected JSON only."
        raw = ask("cross_domain_architecture_transfer_inventor", prompt + repair)
        try:
            return validate_architecture_transfers(
                raw, evidence_packet=packet, target_fact_ids=target_fact_ids,
                max_transfers=max_transfers, target_domain=target_domain,
            )
        except ValueError as exc:
            last_error = str(exc)
    raise ValueError(f"architecture transfer provider failed contract after repair: {last_error}")


__all__ = [
    "AUTHORITY_FIELDS",
    "CommandResult",
    "EVIDENCE_PACKET_VERSION",
    "EvidenceLimits",
    "GitNexusEvidenceAdapter",
    "MECHANISM_QUERY_VERSION",
    "TRANSFER_CONTRACT_VERSION",
    "propose_architecture_transfers",
    "propose_mechanism_queries",
    "validate_architecture_transfers",
    "validate_gitnexus_evidence_packet",
    "validate_mechanism_queries",
]
