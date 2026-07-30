#!/usr/bin/env python3
"""Persistent product-ground-truth and deterministic mission approval gates."""

from __future__ import annotations

import hashlib
import json
import fcntl
import os
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import utc_now


class ProductAlignmentStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.events_path = root / "events.jsonl"

    @staticmethod
    def _fingerprint(value: Any) -> str:
        return hashlib.sha256(
            json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def events(self) -> List[Dict[str, Any]]:
        if not self.events_path.is_file():
            return []
        rows = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def _append_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event)
        payload.setdefault("recorded_at", utc_now())
        payload.setdefault("event_version", "palamedes-product-alignment-event/1")
        identity = {
            key: value for key, value in payload.items() if key != "recorded_at"
        }
        payload.setdefault(
            "event_id", f"alignment-event-{self._fingerprint(identity)[:16]}"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            for line in handle:
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    isinstance(existing, dict)
                    and existing.get("event_id") == payload["event_id"]
                ):
                    return payload
            handle.seek(0, os.SEEK_END)
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return payload

    @staticmethod
    def _empty_state() -> Dict[str, Any]:
        return {
            "alignment_version": "palamedes-product-alignment/1",
            "purposes": [],
            "capabilities": [],
            "constraints": [],
            "integration_gaps": [],
            "product_stage": {},
            "surface_stages": {},
        }

    def _apply_record_to_state(
        self,
        state: Dict[str, Any],
        kind: str,
        payload: Dict[str, Any],
        surface_key: str = "",
    ) -> None:
        row = dict(payload)
        if kind in {"purpose", "capability", "constraint"}:
            row.setdefault("status", "active")
        elif kind == "integration_gap":
            row.setdefault("status", "open")
        if kind == "purpose":
            self._merge_row(state["purposes"], "purpose_id", row)
        elif kind == "capability":
            self._merge_row(state["capabilities"], "capability_id", row)
        elif kind == "constraint":
            row.setdefault("scope", row.pop("surface_key", surface_key))
            self._merge_row(state["constraints"], "constraint_id", row)
        elif kind == "integration_gap":
            self._merge_row(state["integration_gaps"], "gap_id", row)
        elif kind == "stage":
            if surface_key:
                state["surface_stages"][surface_key] = row
            else:
                state["product_stage"] = row

    def project_state(self) -> Dict[str, Any]:
        state = self._empty_state()
        for event in self.events():
            event_type = event.get("event_type")
            if event_type == "candidate_approved":
                payload = dict(event.get("payload", {}))
                payload.setdefault("source_ids", event.get("source_ids", []))
                payload.setdefault("surface_key", event.get("surface_key", ""))
                kind = str(event.get("candidate_type", ""))
                if kind == "integration_gap":
                    payload.setdefault("evidence_ids", payload.pop("source_ids", []))
                if kind == "stage":
                    payload.pop("source_ids", None)
                self._apply_record_to_state(
                    state, kind, payload, str(event.get("surface_key", ""))
                )
            elif event_type == "record_upsert":
                self._apply_record_to_state(
                    state,
                    str(event.get("record_type", "")),
                    dict(event.get("record", {})),
                    str(event.get("surface_key", "")),
                )
            elif event_type == "constraint_expired":
                for row in state["constraints"]:
                    if row.get("constraint_id") == event.get("constraint_id"):
                        row["status"] = "expired_pending_review"
                        row["expiry_evidence_ids"] = event.get(
                            "expiry_evidence_ids", []
                        )
                        row["expired_at"] = event.get("recorded_at")
        return state

    @staticmethod
    def _merge_row(
        rows: List[Dict[str, Any]], id_field: str, incoming: Dict[str, Any]
    ) -> None:
        existing = next(
            (row for row in rows if row.get(id_field) == incoming.get(id_field)),
            None,
        )
        if existing is None:
            rows.append(incoming)
            return
        for source_id in incoming.get("source_ids", incoming.get("evidence_ids", [])):
            target_field = "source_ids" if "source_ids" in incoming else "evidence_ids"
            if source_id not in existing.setdefault(target_field, []):
                existing[target_field].append(source_id)
        statement = str(incoming.get("statement", "")).strip()
        if statement and statement != existing.get("statement"):
            variants = existing.setdefault("statement_variants", [])
            if statement not in variants:
                variants.append(statement)
        for key, value in incoming.items():
            if key not in {"statement", "source_ids", "evidence_ids", "observed_at"}:
                existing[key] = value
        existing["last_merged_at"] = incoming.get("observed_at", utc_now())

    def propose_candidate(
        self,
        *,
        candidate_type: str,
        payload: Dict[str, Any],
        source_ids: List[str],
        surface_key: str = "",
    ) -> Dict[str, Any]:
        if candidate_type not in {
            "purpose",
            "capability",
            "constraint",
            "integration_gap",
            "stage",
        }:
            raise ValueError("unsupported product alignment candidate type")
        if not isinstance(payload, dict) or not payload or not source_ids:
            raise ValueError("alignment candidate requires payload and source_ids")
        identity = {
            "candidate_type": candidate_type,
            "payload": payload,
            "source_ids": sorted(set(source_ids)),
            "surface_key": surface_key,
        }
        candidate = {
            "candidate_id": f"alignment-candidate-{self._fingerprint(identity)[:16]}",
            **identity,
            "status": "proposed",
        }
        self._append_event({"event_type": "candidate_proposed", **candidate})
        return candidate

    def approve_candidate(self, candidate_id: str, *, approver: str) -> Dict[str, Any]:
        if not approver.strip():
            raise ValueError("alignment candidate approval requires approver")
        proposed = [
            row
            for row in self.events()
            if row.get("event_type") == "candidate_proposed"
            and row.get("candidate_id") == candidate_id
        ]
        if not proposed:
            raise ValueError("unknown product alignment candidate")
        candidate = proposed[-1]
        if any(
            row.get("event_type") == "candidate_approved"
            and row.get("candidate_id") == candidate_id
            for row in self.events()
        ):
            return {**candidate, "status": "approved", "idempotent": True}
        self._append_event(
            {
                "event_type": "candidate_approved",
                "candidate_id": candidate_id,
                "candidate_type": candidate["candidate_type"],
                "payload": candidate["payload"],
                "source_ids": candidate["source_ids"],
                "surface_key": candidate.get("surface_key", ""),
                "approver": approver,
            }
        )
        self.save(self.project_state())
        return {**candidate, "status": "approved", "idempotent": False}

    def load(self) -> Dict[str, Any]:
        if self.events_path.is_file():
            return self.project_state()
        if not self.state_path.exists():
            return self._empty_state()
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("product alignment state must be an object")
        return payload

    def save(self, state: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.state_path)

    def record_purpose(
        self,
        *,
        purpose_id: str,
        statement: str,
        source_ids: List[str],
        strength: str = "product_invariant",
        surface_key: str = "",
        _record_event: bool = True,
    ) -> None:
        if strength not in {"hypothesis", "preference", "product_invariant"}:
            raise ValueError("unsupported purpose strength")
        state = self.load()
        incoming = {
            "purpose_id": purpose_id,
            "statement": statement,
            "source_ids": source_ids,
            "strength": strength,
            "surface_key": surface_key,
            "status": "active",
            "observed_at": utc_now(),
        }
        if _record_event:
            self._append_event(
                {
                    "event_type": "record_upsert",
                    "record_type": "purpose",
                    "record": incoming,
                }
            )
            self.save(self.project_state())
        else:
            self._merge_row(state["purposes"], "purpose_id", incoming)
            self.save(state)

    def record_capability(
        self,
        *,
        capability_id: str,
        statement: str,
        source_ids: List[str],
        surface_key: str = "",
        _record_event: bool = True,
    ) -> None:
        state = self.load()
        incoming = {
            "capability_id": capability_id,
            "statement": statement,
            "source_ids": source_ids,
            "surface_key": surface_key,
            "status": "active",
            "observed_at": utc_now(),
        }
        if _record_event:
            self._append_event(
                {
                    "event_type": "record_upsert",
                    "record_type": "capability",
                    "record": incoming,
                }
            )
            self.save(self.project_state())
        else:
            self._merge_row(state["capabilities"], "capability_id", incoming)
            self.save(state)

    def record_integration_gap(
        self,
        *,
        gap_id: str,
        surface_key: str,
        expected_capability_id: str,
        observed_path: str,
        evidence_ids: List[str],
        _record_event: bool = True,
    ) -> None:
        state = self.load()
        if expected_capability_id not in {
            row.get("capability_id") for row in state["capabilities"]
        }:
            raise ValueError("integration gap must reference a known capability")
        state.setdefault("integration_gaps", [])
        incoming = {
            "gap_id": gap_id,
            "surface_key": surface_key,
            "expected_capability_id": expected_capability_id,
            "observed_path": observed_path,
            "evidence_ids": evidence_ids,
            "status": "open",
            "observed_at": utc_now(),
        }
        if _record_event:
            self._append_event(
                {
                    "event_type": "record_upsert",
                    "record_type": "integration_gap",
                    "record": incoming,
                }
            )
            self.save(self.project_state())
        else:
            self._merge_row(state["integration_gaps"], "gap_id", incoming)
            self.save(state)

    def record_constraint(
        self,
        *,
        constraint_id: str,
        statement: str,
        source_ids: List[str],
        scope: str,
        expires_when: str,
        status: str = "active",
        _record_event: bool = True,
    ) -> None:
        if status not in {"active", "expired_pending_review", "retired"}:
            raise ValueError("unsupported constraint status")
        state = self.load()
        incoming = {
            "constraint_id": constraint_id,
            "statement": statement,
            "source_ids": source_ids,
            "scope": scope,
            "expires_when": expires_when,
            "status": status,
            "observed_at": utc_now(),
        }
        if _record_event:
            self._append_event(
                {
                    "event_type": "record_upsert",
                    "record_type": "constraint",
                    "record": incoming,
                }
            )
            self.save(self.project_state())
        else:
            self._merge_row(state["constraints"], "constraint_id", incoming)
            self.save(state)

    def set_product_stage(
        self,
        *,
        stage: str,
        required_journey_ids: List[str],
        evidence_ids: List[str],
        surface_key: str = "",
        _record_event: bool = True,
    ) -> None:
        if stage not in {"prototype", "alpha", "beta", "rc", "production"}:
            raise ValueError("unsupported product stage")
        state = self.load()
        incoming = {
            "stage": stage,
            "required_journey_ids": required_journey_ids,
            "evidence_ids": evidence_ids,
            "observed_at": utc_now(),
        }
        if _record_event:
            self._append_event(
                {
                    "event_type": "record_upsert",
                    "record_type": "stage",
                    "surface_key": surface_key,
                    "record": incoming,
                }
            )
            self.save(self.project_state())
        else:
            if surface_key:
                state.setdefault("surface_stages", {})[surface_key] = incoming
            else:
                state["product_stage"] = incoming
            self.save(state)

    def mark_constraint_expired(
        self, constraint_id: str, *, expiry_evidence_ids: List[str]
    ) -> None:
        if not expiry_evidence_ids:
            raise ValueError("constraint expiry requires evidence")
        state = self.load()
        for row in state["constraints"]:
            if row.get("constraint_id") == constraint_id:
                row["status"] = "expired_pending_review"
                row["expiry_evidence_ids"] = expiry_evidence_ids
                row["expired_at"] = utc_now()
                self._append_event(
                    {
                        "event_type": "constraint_expired",
                        "constraint_id": constraint_id,
                        "expiry_evidence_ids": expiry_evidence_ids,
                    }
                )
                self.save(self.project_state())
                return
        raise ValueError("unknown constraint")

    def active_context(self) -> Dict[str, Any]:
        state = self.load()
        context = {
            "purposes": [
                row for row in state["purposes"] if row.get("status") == "active"
            ],
            "capabilities": [
                row for row in state["capabilities"] if row.get("status") == "active"
            ],
            "constraints": [
                row
                for row in state["constraints"]
                if row.get("status") in {"active", "expired_pending_review"}
            ],
            "integration_gaps": [
                row
                for row in state.get("integration_gaps", [])
                if row.get("status") == "open"
            ],
            "product_stage": state.get("product_stage", {}),
            "surface_stages": state.get("surface_stages", {}),
        }
        surface_keys = sorted(
            {
                str(row.get("surface_key", "")).strip()
                for field in ("purposes", "capabilities", "integration_gaps")
                for row in context[field]
                if str(row.get("surface_key", "")).strip()
            }
            | set(context["surface_stages"])
        )
        context["surfaces"] = {
            surface: {
                "purposes": [
                    row
                    for row in context["purposes"]
                    if row.get("surface_key") == surface
                ],
                "capabilities": [
                    row
                    for row in context["capabilities"]
                    if row.get("surface_key") == surface
                ],
                "integration_gaps": [
                    row
                    for row in context["integration_gaps"]
                    if row.get("surface_key") == surface
                ],
                "product_stage": context["surface_stages"].get(surface, {}),
            }
            for surface in surface_keys
        }
        return context


def validate_alignment_response(
    contract: Dict[str, Any],
    store: ProductAlignmentStore,
    *,
    outcome_count: int = 0,
) -> None:
    context = store.active_context()
    if (
        outcome_count >= 5
        and not context["purposes"]
        and contract.get("work_scale") == "micro"
    ):
        raise ValueError(
            "mission approval blocked: product purpose remains ungrounded after "
            "repeated delivery; run a component-or-higher purpose discovery mission"
        )
    surface_key = str(contract.get("surface_key", "")).strip()

    def relevant(row: Dict[str, Any]) -> bool:
        recorded = str(row.get("surface_key", row.get("scope", ""))).strip()
        return not recorded or not surface_key or recorded == surface_key

    purposes = {
        row["purpose_id"]: row
        for row in context["purposes"]
        if row.get("strength") == "product_invariant" and relevant(row)
    }
    capabilities = {
        row["capability_id"]: row for row in context["capabilities"] if relevant(row)
    }
    expired = {
        row["constraint_id"]
        for row in context["constraints"]
        if row.get("status") == "expired_pending_review" and relevant(row)
    }
    integration_gaps = {
        row["gap_id"]: row for row in context["integration_gaps"] if relevant(row)
    }
    response = contract.get("product_alignment_response")
    if (
        purposes
        or capabilities
        or expired
        or integration_gaps
        or context["product_stage"]
    ) and not isinstance(response, dict):
        raise ValueError(
            "mission approval blocked: product alignment response is required"
        )
    if not isinstance(response, dict):
        return

    purpose_rows = response.get("purposes", [])
    if not isinstance(purpose_rows, list):
        raise ValueError("product alignment purposes must be an array")
    acknowledged = {
        row.get("purpose_id"): row for row in purpose_rows if isinstance(row, dict)
    }
    missing = sorted(set(purposes) - set(acknowledged))
    if missing:
        raise ValueError(
            "mission approval blocked by unaddressed product invariants: "
            + ", ".join(missing)
        )
    conflicts = [
        purpose_id
        for purpose_id, row in acknowledged.items()
        if purpose_id in purposes and row.get("effect") == "conflicts"
    ]
    unknown = [
        purpose_id
        for purpose_id, row in acknowledged.items()
        if purpose_id in purposes and row.get("effect") == "unknown"
    ]
    if conflicts:
        raise ValueError(
            "mission approval blocked by product-purpose conflict: "
            + ", ".join(conflicts)
        )
    if unknown and contract.get("work_scale") == "micro":
        raise ValueError(
            "mission approval blocked: unknown product alignment requires a "
            "component-or-higher bounded audit"
        )

    reuse = response.get("capability_reuse", {})
    relevant = (
        set(reuse.get("relevant_capability_ids", []))
        if isinstance(reuse, dict)
        else set()
    )
    missing_capabilities = sorted(set(capabilities) - relevant)
    if missing_capabilities:
        raise ValueError(
            "mission approval blocked: existing capabilities were not evaluated: "
            + ", ".join(missing_capabilities)
        )
    if capabilities and reuse.get("decision") in {"new", "unknown"}:
        if (
            not reuse.get("rejection_evidence_ids")
            or not str(reuse.get("rationale", "")).strip()
        ):
            raise ValueError(
                "mission approval blocked: greenfield work requires evidence for "
                "rejecting relevant existing capabilities"
            )

    gap_response = response.get("integration_gaps", [])
    if not isinstance(gap_response, list):
        raise ValueError("product alignment integration_gaps must be an array")
    gap_rows = {row.get("gap_id"): row for row in gap_response if isinstance(row, dict)}
    missing_gaps = sorted(set(integration_gaps) - set(gap_rows))
    if missing_gaps:
        raise ValueError(
            "mission approval blocked by unaddressed capability bypasses: "
            + ", ".join(missing_gaps)
        )
    invalid_gap_actions = [
        gap_id
        for gap_id, row in gap_rows.items()
        if gap_id in integration_gaps
        and row.get("action") not in {"audit", "resolve", "accept_debt"}
    ]
    if invalid_gap_actions:
        raise ValueError(
            "capability bypass response requires audit, resolve, or accept_debt"
        )

    constraint_review = response.get("constraint_review", {})
    reviewed = (
        set(constraint_review.get("reviewed_constraint_ids", []))
        if isinstance(constraint_review, dict)
        else set()
    )
    if expired - reviewed:
        raise ValueError(
            "mission approval blocked by expired constraints pending review: "
            + ", ".join(sorted(expired - reviewed))
        )

    requested_stage = response.get("stage_claim", {})
    if isinstance(requested_stage, dict) and requested_stage.get("advances_stage"):
        required = set(context["product_stage"].get("required_journey_ids", []))
        supplied = set(requested_stage.get("journey_evidence_ids", []))
        if required - supplied:
            raise ValueError(
                "mission approval blocked: product-stage claim lacks journey evidence: "
                + ", ".join(sorted(required - supplied))
            )
