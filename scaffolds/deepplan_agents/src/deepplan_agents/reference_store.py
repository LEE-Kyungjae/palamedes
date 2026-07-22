#!/usr/bin/env python3
"""Persistent reference-pattern storage for the DeepPlan agent scaffold."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from deepplan_agents.reference_rag import normalize_reference_pattern


SCHEMA_VERSION = 1


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def reference_content_hash(pattern: Dict[str, Any]) -> str:
    content = {key: value for key, value in pattern.items() if key != "reference_id"}
    return hashlib.sha256(_canonical_json(content).encode("utf-8")).hexdigest()


class ReferenceStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(self.path))
        connection.row_factory = sqlite3.Row
        try:
            self._ensure_schema(connection)
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _ensure_schema(self, connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reference_patterns (
                reference_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                source_url TEXT NOT NULL,
                source_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE UNIQUE INDEX IF NOT EXISTS reference_patterns_content_hash
                ON reference_patterns(content_hash);
            CREATE INDEX IF NOT EXISTS reference_patterns_source_type
                ON reference_patterns(source_type);
            CREATE INDEX IF NOT EXISTS reference_patterns_source_url
                ON reference_patterns(source_url);
            """
        )
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES('schema_version', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (str(SCHEMA_VERSION),),
        )

    def upsert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        pattern = normalize_reference_pattern(item)
        digest = reference_content_hash(pattern)
        with self._connection() as connection:
            duplicate = connection.execute(
                "SELECT reference_id, payload_json FROM reference_patterns WHERE content_hash = ?",
                (digest,),
            ).fetchone()
            if duplicate is not None and duplicate["reference_id"] != pattern["reference_id"]:
                return {
                    "status": "duplicate",
                    "reference_id": duplicate["reference_id"],
                    "pattern": json.loads(duplicate["payload_json"]),
                }
            existing = connection.execute(
                "SELECT content_hash FROM reference_patterns WHERE reference_id = ?",
                (pattern["reference_id"],),
            ).fetchone()
            status = "unchanged" if existing is not None and existing["content_hash"] == digest else ("updated" if existing else "created")
            connection.execute(
                """
                INSERT INTO reference_patterns(reference_id, content_hash, source_url, source_type, payload_json)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(reference_id) DO UPDATE SET
                    content_hash=excluded.content_hash,
                    source_url=excluded.source_url,
                    source_type=excluded.source_type,
                    payload_json=excluded.payload_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (pattern["reference_id"], digest, pattern["source_url"], pattern["source_type"], _canonical_json(pattern)),
            )
        return {"status": status, "reference_id": pattern["reference_id"], "pattern": pattern}

    def ingest(self, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        results = [self.upsert(item) for item in items]
        counts = {status: sum(result["status"] == status for result in results) for status in ["created", "updated", "unchanged", "duplicate"]}
        return {"total": len(results), "counts": counts, "results": results}

    def list(self, *, source_type: str = "", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        query = "SELECT payload_json FROM reference_patterns"
        parameters: List[Any] = []
        if source_type:
            query += " WHERE source_type = ?"
            parameters.append(source_type)
        query += " ORDER BY updated_at DESC, reference_id ASC"
        if limit is not None:
            query += " LIMIT ?"
            parameters.append(max(0, limit))
        with self._connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def get(self, reference_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT payload_json FROM reference_patterns WHERE reference_id = ?",
                (reference_id,),
            ).fetchone()
        return json.loads(row["payload_json"]) if row is not None else None

    def count(self) -> int:
        with self._connection() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM reference_patterns").fetchone()
        return int(row["count"])

    def health(self) -> Dict[str, Any]:
        try:
            with self._connection() as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                schema_row = connection.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
                count_row = connection.execute("SELECT COUNT(*) AS count FROM reference_patterns").fetchone()
            issues = []
            if integrity != "ok":
                issues.append(f"sqlite_integrity:{integrity}")
            schema_version = int(schema_row["value"]) if schema_row is not None else 0
            if schema_version != SCHEMA_VERSION:
                issues.append(f"schema_version:{schema_version}")
            return {
                "status": "ok" if not issues else "degraded",
                "issues": issues,
                "schema_version": schema_version,
                "reference_count": int(count_row["count"]),
                "path": str(self.path),
            }
        except (OSError, sqlite3.Error, ValueError) as exc:
            return {
                "status": "error",
                "issues": [str(exc)],
                "schema_version": 0,
                "reference_count": 0,
                "path": str(self.path),
            }
