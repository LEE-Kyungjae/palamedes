#!/usr/bin/env python3
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Callable, Dict, List, Optional


class PlanConflictError(ValueError):
    def __init__(self, current_fingerprint: str) -> None:
        super().__init__("plan fingerprint mismatch")
        self.current_fingerprint = current_fingerprint


class FilePlanStore:
    def __init__(
        self,
        *,
        state_dir: Path,
        plan_path: Path,
        decisions_path: Path,
        risks_path: Path,
        events_path: Path,
        revisions_path: Path,
        default_plan_factory: Callable[[], Dict],
        migrate_plan: Callable[[Dict], Dict],
        now_iso: Callable[[], str],
        plan_fingerprint: Callable[[Dict], str],
        normalize_fingerprint: Callable[[Optional[str]], str],
        ensure_valid_plan: Callable[[Dict], Dict],
        qa_autoreplan_result: Callable[..., Dict],
        revision_metadata_builder: Optional[Callable[[Dict], Dict]] = None,
        retention_limits: Optional[Dict[str, int]] = None,
        lock: Optional[threading.RLock] = None,
    ) -> None:
        self.state_dir = state_dir
        self.plan_path = plan_path
        self.decisions_path = decisions_path
        self.risks_path = risks_path
        self.events_path = events_path
        self.revisions_path = revisions_path
        self.default_plan_factory = default_plan_factory
        self.migrate_plan = migrate_plan
        self.now_iso = now_iso
        self.plan_fingerprint = plan_fingerprint
        self.normalize_fingerprint = normalize_fingerprint
        self.ensure_valid_plan = ensure_valid_plan
        self.qa_autoreplan_result = qa_autoreplan_result
        self.revision_metadata_builder = revision_metadata_builder
        self.retention_limits = dict(retention_limits or {})
        self.lock = lock or threading.RLock()

    def ensure_state(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        for path in [self.decisions_path, self.risks_path, self.events_path, self.revisions_path]:
            if not path.exists():
                path.write_text("", encoding="utf-8")
        if not self.plan_path.exists():
            self.plan_path.write_text(json.dumps(self.default_plan_factory(), indent=2), encoding="utf-8")

    def load_plan_unlocked(self) -> Dict:
        self.ensure_state()
        original_plan = json.loads(self.plan_path.read_text(encoding="utf-8"))
        return self.migrate_plan(json.loads(json.dumps(original_plan)))

    def load_plan(self) -> Dict:
        with self.lock:
            return self.load_plan_unlocked()

    def atomic_write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
                tmp.write(text)
                tmp.flush()
                os.fsync(tmp.fileno())
                temp_path = Path(tmp.name)
            os.replace(temp_path, path)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def save_plan_unlocked(self, plan: Dict) -> None:
        plan["updated_at"] = self.now_iso()
        self.atomic_write_text(self.plan_path, json.dumps(plan, indent=2, ensure_ascii=False))

    def save_plan(self, plan: Dict) -> None:
        with self.lock:
            self.save_plan_unlocked(plan)

    def save_validated_plan_unlocked(self, plan: Dict) -> None:
        self.ensure_valid_plan(plan)
        self.save_plan_unlocked(plan)

    def append_jsonl_unlocked(self, path: Path, payload: Dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._best_effort_prune_unlocked(path)

    def append_jsonl(self, path: Path, payload: Dict) -> None:
        with self.lock:
            self.append_jsonl_unlocked(path, payload)

    def _retention_label_for_path(self, path: Path) -> str:
        if path == self.events_path:
            return "events"
        if path == self.revisions_path:
            return "revisions"
        if path == self.decisions_path:
            return "decisions"
        if path == self.risks_path:
            return "risks"
        return path.name

    def _retention_limit_for_path(self, path: Path) -> int:
        label = self._retention_label_for_path(path)
        limit = int(self.retention_limits.get(label, 0) or 0)
        if label == "revisions" and limit > 0:
            return max(2, limit)
        return limit

    def prune_jsonl_unlocked(self, path: Path, keep_latest: int) -> Dict:
        label = self._retention_label_for_path(path)
        if keep_latest <= 0:
            return {
                "path": str(path),
                "label": label,
                "retention_limit": 0,
                "before_count": 0,
                "after_count": 0,
                "pruned_lines": 0,
                "pruned": False,
            }
        if not path.exists():
            return {
                "path": str(path),
                "label": label,
                "retention_limit": keep_latest,
                "before_count": 0,
                "after_count": 0,
                "pruned_lines": 0,
                "pruned": False,
            }
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        before_count = len(lines)
        if before_count <= keep_latest:
            return {
                "path": str(path),
                "label": label,
                "retention_limit": keep_latest,
                "before_count": before_count,
                "after_count": before_count,
                "pruned_lines": 0,
                "pruned": False,
            }
        kept_lines = lines[-keep_latest:]
        body = "\n".join(kept_lines) + "\n"
        self.atomic_write_text(path, body)
        return {
            "path": str(path),
            "label": label,
            "retention_limit": keep_latest,
            "before_count": before_count,
            "after_count": len(kept_lines),
            "pruned_lines": before_count - len(kept_lines),
            "pruned": True,
        }

    def _best_effort_prune_unlocked(self, path: Path) -> None:
        keep_latest = self._retention_limit_for_path(path)
        if keep_latest <= 0:
            return
        try:
            self.prune_jsonl_unlocked(path, keep_latest)
        except Exception:
            return

    def maintenance_report_unlocked(self, apply: bool = False) -> Dict:
        logs: Dict[str, Dict] = {}
        for path in [self.events_path, self.revisions_path]:
            label = self._retention_label_for_path(path)
            keep_latest = self._retention_limit_for_path(path)
            if apply:
                report = self.prune_jsonl_unlocked(path, keep_latest)
                report["line_count"] = report["after_count"]
                report["over_limit_by"] = max(0, report["after_count"] - keep_latest) if keep_latest > 0 else 0
            else:
                line_count = 0
                if path.exists():
                    line_count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
                report = {
                    "path": str(path),
                    "label": label,
                    "retention_limit": keep_latest,
                    "line_count": line_count,
                    "over_limit_by": max(0, line_count - keep_latest) if keep_latest > 0 else 0,
                    "pruned": False,
                    "pruned_lines": 0,
                }
            logs[label] = report
        return {"applied": apply, "logs": logs}

    def maintenance_report(self, apply: bool = False) -> Dict:
        with self.lock:
            return self.maintenance_report_unlocked(apply=apply)

    def make_revision_entry(self, plan: Dict, source: str, reason: str = "", previous_fingerprint: str = "") -> Dict:
        fingerprint = self.plan_fingerprint(plan)
        ts = self.now_iso()
        entry = {
            "revision_id": f"{ts}_{fingerprint[:12]}",
            "ts": ts,
            "source": source,
            "reason": reason,
            "fingerprint": fingerprint,
            "previous_fingerprint": previous_fingerprint,
            "plan": json.loads(json.dumps(plan)),
        }
        if self.revision_metadata_builder:
            entry["metadata"] = self.revision_metadata_builder(plan)
        return entry

    def append_revision_unlocked(self, plan: Dict, source: str, reason: str = "", previous_fingerprint: str = "") -> Dict:
        entry = self.make_revision_entry(plan, source, reason=reason, previous_fingerprint=previous_fingerprint)
        self.append_jsonl_unlocked(self.revisions_path, entry)
        return entry

    def append_revision(self, plan: Dict, source: str, reason: str = "", previous_fingerprint: str = "") -> Dict:
        with self.lock:
            return self.append_revision_unlocked(plan, source, reason=reason, previous_fingerprint=previous_fingerprint)

    def mutate_plan_state(
        self,
        mutate_fn,
        *,
        event_payloads: Optional[List[Dict]] = None,
        include_autoreplan: bool = False,
        expected_fingerprint: Optional[str] = None,
        revision_source: str = "mutate_plan_state",
        revision_reason: str = "",
    ):
        with self.lock:
            plan = self.load_plan_unlocked()
            current_fingerprint = self.plan_fingerprint(plan)
            normalized_expected = self.normalize_fingerprint(expected_fingerprint)
            if normalized_expected and normalized_expected != current_fingerprint:
                raise PlanConflictError(current_fingerprint)
            mutate_fn(plan)
            self.save_validated_plan_unlocked(plan)
            revision_entry = self.append_revision_unlocked(
                plan,
                revision_source,
                reason=revision_reason,
                previous_fingerprint=current_fingerprint,
            )
            for payload in event_payloads or []:
                self.append_jsonl_unlocked(self.events_path, payload)
            if include_autoreplan:
                return self.qa_autoreplan_result(plan, base_revision_entry=revision_entry)
            return plan

    def read_jsonl(self, path: Path) -> List[Dict]:
        if not path.exists():
            return []
        items: List[Dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items

    def jsonl_health(self, path: Path) -> Dict:
        retention_limit = self._retention_limit_for_path(path)
        if not path.exists():
            return {
                "path": str(path),
                "exists": False,
                "line_count": 0,
                "valid_objects": 0,
                "invalid_lines": 0,
                "last_error": "",
                "retention_limit": retention_limit,
                "over_limit_by": 0,
            }
        line_count = 0
        valid_objects = 0
        invalid_lines = 0
        last_error = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            line_count += 1
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                invalid_lines += 1
                last_error = str(exc)
                continue
            if isinstance(payload, dict):
                valid_objects += 1
            else:
                invalid_lines += 1
                last_error = "line is not a JSON object"
        return {
            "path": str(path),
            "exists": True,
            "line_count": line_count,
            "valid_objects": valid_objects,
            "invalid_lines": invalid_lines,
            "last_error": last_error,
            "retention_limit": retention_limit,
            "over_limit_by": max(0, line_count - retention_limit) if retention_limit > 0 else 0,
        }
