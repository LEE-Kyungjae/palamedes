#!/usr/bin/env python3
"""Content-addressed evidence storage and non-destructive retention inventory."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List


POLICY_VERSION = "palamedes-storage-policy/1"
IMMUTABLE_PREFIXES = (
    "missions/handoffs/",
    "missions/outcomes.jsonl",
    "missions/lifecycle-events.jsonl",
    "missions/outcome-gates.jsonl",
    "events.jsonl",
    "revisions.jsonl",
)
CACHE_PREFIXES = ("observations/", "visions/checkpoints/", "vision-scouts/checkpoints/")
SENSITIVE_PREFIXES = ("chat/", "thoughts/experiences/")


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _classification(relative: str) -> str:
    if any(relative.startswith(prefix) for prefix in IMMUTABLE_PREFIXES):
        return "immutable_ledger"
    if any(relative.startswith(prefix) for prefix in CACHE_PREFIXES):
        return "regenerable_cache"
    if any(relative.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
        return "sensitive_history"
    if relative.startswith("blobs/sha256/"):
        return "content_addressed_blob"
    return "retained_state"


class ContentAddressedStore:
    def __init__(self, state_dir: Path) -> None:
        self.root = state_dir / "blobs" / "sha256"

    def put_bytes(
        self, data: bytes, *, media_type: str, source_ids: List[str]
    ) -> Dict[str, Any]:
        if not media_type.strip() or not source_ids:
            raise ValueError("blob requires media_type and source_ids")
        digest = hashlib.sha256(data).hexdigest()
        path = self.root / digest[:2] / digest
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(path)
        return {
            "blob_ref_version": "palamedes-blob-ref/1",
            "algorithm": "sha256",
            "sha256": digest,
            "size_bytes": len(data),
            "media_type": media_type,
            "source_ids": sorted(set(source_ids)),
            "relative_path": str(path.relative_to(self.root.parent.parent)),
        }

    def verify(self, reference: Dict[str, Any]) -> Dict[str, Any]:
        digest = str(reference.get("sha256", ""))
        if len(digest) != 64:
            return {"valid": False, "reason": "invalid_digest"}
        path = self.root / digest[:2] / digest
        if not path.is_file():
            return {"valid": False, "reason": "missing_blob", "path": str(path)}
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        expected_size = reference.get("size_bytes")
        valid = actual == digest and expected_size == len(data)
        return {
            "valid": valid,
            "reason": "verified" if valid else "checksum_or_size_mismatch",
            "path": str(path),
            "actual_size_bytes": len(data),
            "actual_sha256": actual,
        }


def inventory_storage(state_dir: Path) -> Dict[str, Any]:
    files = []
    by_digest: Dict[str, List[Dict[str, Any]]] = {}
    section_bytes: Dict[str, int] = {}
    class_counts: Dict[str, int] = {}
    class_bytes: Dict[str, int] = {}
    if state_dir.is_dir():
        for path in sorted(state_dir.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            relative = str(path.relative_to(state_dir))
            digest = hashlib.sha256(data).hexdigest()
            classification = _classification(relative)
            row = {
                "path": relative,
                "size_bytes": len(data),
                "sha256": digest,
                "classification": classification,
            }
            files.append(row)
            by_digest.setdefault(digest, []).append(row)
            section = relative.split("/", 1)[0]
            section_bytes[section] = section_bytes.get(section, 0) + len(data)
            class_counts[classification] = class_counts.get(classification, 0) + 1
            class_bytes[classification] = class_bytes.get(classification, 0) + len(data)
    duplicates = []
    reclaimable = 0
    for digest, rows in by_digest.items():
        if len(rows) < 2 or rows[0]["size_bytes"] == 0:
            continue
        recover = rows[0]["size_bytes"] * (len(rows) - 1)
        reclaimable += recover
        duplicates.append(
            {
                "sha256": digest,
                "size_bytes": rows[0]["size_bytes"],
                "copies": len(rows),
                "reclaimable_bytes": recover,
                "paths": [row["path"] for row in rows],
                "action": "eligible_after_consumer_migration",
            }
        )
    logical_bytes = sum(row["size_bytes"] for row in files)
    core = {
        "storage_policy_version": POLICY_VERSION,
        "read_only": True,
        "summary": {
            "files": len(files),
            "logical_bytes": logical_bytes,
            "unique_content_bytes": logical_bytes - reclaimable,
            "duplicate_reclaimable_bytes": reclaimable,
            "duplicate_groups": len(duplicates),
        },
        "classification_counts": dict(sorted(class_counts.items())),
        "classification_bytes": dict(sorted(class_bytes.items())),
        "section_bytes": dict(
            sorted(section_bytes.items(), key=lambda item: item[1], reverse=True)
        ),
        "duplicate_groups": sorted(
            duplicates, key=lambda row: row["reclaimable_bytes"], reverse=True
        ),
        "retention": {
            "immutable_ledger": "never delete; append corrections and verify references",
            "regenerable_cache": "eligible for bounded TTL only after a fresh replacement exists",
            "sensitive_history": "explicit retention window and redaction review required",
            "content_addressed_blob": "retain while referenced; delete only after zero-reference proof",
            "retained_state": "retain until a versioned migration defines replacement semantics",
        },
        "mutation_performed": False,
    }
    core["inventory_fingerprint"] = _fingerprint(core)
    return core
