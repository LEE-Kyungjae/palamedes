#!/usr/bin/env python3
"""Persistent product-ground-truth and deterministic mission approval gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import utc_now


class ProductAlignmentStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "state.json"

    def load(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {
                "alignment_version": "palamedes-product-alignment/1",
                "purposes": [],
                "capabilities": [],
                "constraints": [],
                "integration_gaps": [],
                "product_stage": {},
            }
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
    ) -> None:
        if strength not in {"hypothesis", "preference", "product_invariant"}:
            raise ValueError("unsupported purpose strength")
        state = self.load()
        state["purposes"] = [
            row for row in state["purposes"] if row.get("purpose_id") != purpose_id
        ]
        state["purposes"].append(
            {
                "purpose_id": purpose_id,
                "statement": statement,
                "source_ids": source_ids,
                "strength": strength,
                "surface_key": surface_key,
                "status": "active",
                "observed_at": utc_now(),
            }
        )
        self.save(state)

    def record_capability(
        self,
        *,
        capability_id: str,
        statement: str,
        source_ids: List[str],
        surface_key: str = "",
    ) -> None:
        state = self.load()
        state["capabilities"] = [
            row
            for row in state["capabilities"]
            if row.get("capability_id") != capability_id
        ]
        state["capabilities"].append(
            {
                "capability_id": capability_id,
                "statement": statement,
                "source_ids": source_ids,
                "surface_key": surface_key,
                "status": "active",
                "observed_at": utc_now(),
            }
        )
        self.save(state)

    def record_integration_gap(
        self,
        *,
        gap_id: str,
        surface_key: str,
        expected_capability_id: str,
        observed_path: str,
        evidence_ids: List[str],
    ) -> None:
        state = self.load()
        if expected_capability_id not in {
            row.get("capability_id") for row in state["capabilities"]
        }:
            raise ValueError("integration gap must reference a known capability")
        state.setdefault("integration_gaps", [])
        state["integration_gaps"] = [
            row for row in state["integration_gaps"] if row.get("gap_id") != gap_id
        ]
        state["integration_gaps"].append(
            {
                "gap_id": gap_id,
                "surface_key": surface_key,
                "expected_capability_id": expected_capability_id,
                "observed_path": observed_path,
                "evidence_ids": evidence_ids,
                "status": "open",
                "observed_at": utc_now(),
            }
        )
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
    ) -> None:
        if status not in {"active", "expired_pending_review", "retired"}:
            raise ValueError("unsupported constraint status")
        state = self.load()
        state["constraints"] = [
            row
            for row in state["constraints"]
            if row.get("constraint_id") != constraint_id
        ]
        state["constraints"].append(
            {
                "constraint_id": constraint_id,
                "statement": statement,
                "source_ids": source_ids,
                "scope": scope,
                "expires_when": expires_when,
                "status": status,
                "observed_at": utc_now(),
            }
        )
        self.save(state)

    def set_product_stage(
        self, *, stage: str, required_journey_ids: List[str], evidence_ids: List[str]
    ) -> None:
        if stage not in {"prototype", "alpha", "beta", "rc", "production"}:
            raise ValueError("unsupported product stage")
        state = self.load()
        state["product_stage"] = {
            "stage": stage,
            "required_journey_ids": required_journey_ids,
            "evidence_ids": evidence_ids,
            "observed_at": utc_now(),
        }
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
                self.save(state)
                return
        raise ValueError("unknown constraint")

    def active_context(self) -> Dict[str, Any]:
        state = self.load()
        return {
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
        }


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
        row["capability_id"]: row
        for row in context["capabilities"]
        if relevant(row)
    }
    expired = {
        row["constraint_id"]
        for row in context["constraints"]
        if row.get("status") == "expired_pending_review" and relevant(row)
    }
    integration_gaps = {
        row["gap_id"]: row
        for row in context["integration_gaps"]
        if relevant(row)
    }
    response = contract.get("product_alignment_response")
    if (purposes or capabilities or expired or integration_gaps or context["product_stage"]) and not isinstance(
        response, dict
    ):
        raise ValueError(
            "mission approval blocked: product alignment response is required"
        )
    if not isinstance(response, dict):
        return

    purpose_rows = response.get("purposes", [])
    if not isinstance(purpose_rows, list):
        raise ValueError("product alignment purposes must be an array")
    acknowledged = {
        row.get("purpose_id"): row
        for row in purpose_rows
        if isinstance(row, dict)
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
    relevant = set(reuse.get("relevant_capability_ids", [])) if isinstance(reuse, dict) else set()
    missing_capabilities = sorted(set(capabilities) - relevant)
    if missing_capabilities:
        raise ValueError(
            "mission approval blocked: existing capabilities were not evaluated: "
            + ", ".join(missing_capabilities)
        )
    if capabilities and reuse.get("decision") in {"new", "unknown"}:
        if not reuse.get("rejection_evidence_ids") or not str(
            reuse.get("rationale", "")
        ).strip():
            raise ValueError(
                "mission approval blocked: greenfield work requires evidence for "
                "rejecting relevant existing capabilities"
            )

    gap_response = response.get("integration_gaps", [])
    if not isinstance(gap_response, list):
        raise ValueError("product alignment integration_gaps must be an array")
    gap_rows = {
        row.get("gap_id"): row for row in gap_response if isinstance(row, dict)
    }
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
