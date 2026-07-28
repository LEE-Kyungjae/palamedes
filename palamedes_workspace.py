#!/usr/bin/env python3
"""Global workspace registry for one Palamedes installation and many projects."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import utc_now


def default_palamedes_home() -> Path:
    explicit = os.environ.get("PALAMEDES_HOME", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    return (Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share") / "palamedes"


def _workspace_id(path: Path) -> str:
    return "ws-" + hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]


def _valid_name(name: str) -> str:
    value = name.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value):
        raise ValueError("workspace name must use 1-64 letters, numbers, dot, underscore, or hyphen")
    return value


class WorkspaceRegistry:
    def __init__(self, home: Path | None = None) -> None:
        self.home = (home or default_palamedes_home()).expanduser()
        self.path = self.home / "workspaces.json"

    def _load(self) -> Dict[str, Any]:
        if not self.path.is_file():
            return {"registry_version": "palamedes-workspace-registry/1", "workspaces": {}}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or not isinstance(value.get("workspaces"), dict):
            raise ValueError(f"invalid workspace registry: {self.path}")
        return value

    def _save(self, registry: Dict[str, Any]) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.path)

    def register(self, name: str, path: Path) -> Dict[str, Any]:
        name = _valid_name(name)
        root = path.expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"workspace path is not a directory: {root}")
        registry = self._load()
        workspaces = registry["workspaces"]
        existing = workspaces.get(name)
        if isinstance(existing, dict) and Path(str(existing.get("path", ""))) != root:
            raise ValueError(f"workspace name already points elsewhere: {name}")
        for other_name, row in workspaces.items():
            if other_name != name and isinstance(row, dict) and Path(str(row.get("path", ""))) == root:
                raise ValueError(f"workspace path is already registered as {other_name}")
        metadata_path = root / ".palamedes" / "workspace.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        workspace_id = str(existing.get("workspace_id")) if isinstance(existing, dict) and existing.get("workspace_id") else _workspace_id(root)
        record = {"workspace_id": workspace_id, "name": name, "path": str(root), "state_dir": str(root / ".palamedes"), "registered_at": utc_now()}
        metadata_path.write_text(json.dumps({"workspace_version": "palamedes-workspace/1", **record}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        workspaces[name] = record
        registry["updated_at"] = utc_now()
        self._save(registry)
        return record

    def resolve(self, name_or_path: str) -> Path:
        value = name_or_path.strip()
        if not value:
            raise ValueError("workspace name or path is required")
        registry = self._load()
        row = registry["workspaces"].get(value)
        if isinstance(row, dict):
            path = Path(str(row.get("path", ""))).expanduser()
            if not path.is_dir():
                raise ValueError(f"registered workspace path is unavailable: {path}")
            return path.resolve()
        candidate = Path(value).expanduser()
        if candidate.is_dir():
            return candidate.resolve()
        raise ValueError(f"unknown workspace: {value}")

    def list(self) -> List[Dict[str, Any]]:
        return [dict(row) for _, row in sorted(self._load()["workspaces"].items()) if isinstance(row, dict)]

    def remove(self, name: str) -> Dict[str, Any]:
        registry = self._load()
        row = registry["workspaces"].pop(name, None)
        if not isinstance(row, dict):
            raise ValueError(f"unknown registered workspace: {name}")
        registry["updated_at"] = utc_now()
        self._save(registry)
        return row
