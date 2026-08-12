#!/usr/bin/env python3
"""Partitioned product cognition with host-enforced independence.

This module is intentionally isolated from the chat, watch, and opportunity
pipelines.  It provides a small protocol host around an ``ask(role, prompt)``
callable.  The host, rather than a model, owns evidence routing, candidate
identity, freezing, blinding, selection validation, and final issuance.

The protocol has three non-substitutable inventor assignments:

* ``product_opportunity_inventor`` discovers an unasked product/business move
  from local signals rather than returning a code-cleanup suggestion.
* ``cross_domain_architecture_analogist`` transfers a causal mechanism from an
  unrelated source pressure, with explicit adaptation and transfer limits.
* ``failure_experienced_operator`` may claim a failure-earned boundary only
  from explicit adverse evidence.  With no such evidence the host forces an
  abstention and does not ask the role to simulate experience.

All returned mappings and sequences are recursively immutable.  Call
``thaw(value)`` when a mutable JSON-compatible copy is deliberately needed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple


COGNITION_VERSION = "palamedes-partitioned-product-cognition/3"

PRODUCT_OPPORTUNITY_INVENTOR = "product_opportunity_inventor"
CROSS_DOMAIN_ARCHITECTURE_ANALOGIST = "cross_domain_architecture_analogist"
FAILURE_EXPERIENCED_OPERATOR = "failure_experienced_operator"
INVENTOR_ROLES: Tuple[str, ...] = (
    PRODUCT_OPPORTUNITY_INVENTOR,
    CROSS_DOMAIN_ARCHITECTURE_ANALOGIST,
    FAILURE_EXPERIENCED_OPERATOR,
)

BLINDED_ADVERSARY_ROLE = "blinded_product_cognition_adversary"
SELECTOR_ROLE = "product_cognition_selector"
SELECTOR_MODES = {
    "commit",
    "bounded_exploration",
    "discriminating_probe",
    "defer",
}

PROBE_KINDS = {
    "behavioral_exposure",
    "shadow_operation",
    "prototype_test",
    "data_query",
}
PROBE_TERMINAL_OUTPUTS = {
    "observed_actor_response",
    "observed_system_behavior",
    "measured_state_change",
}

_COMMON_CANDIDATE_FIELDS = (
    "output_kind",
    "title",
    "opportunity_thesis",
    "beneficiary",
    "observed_signal",
    "product_mechanism",
    "behavior_change",
    "business_effect",
    "product_opportunity_lineage",
    "second_order_effects",
    "operating_burden",
    "authority",
    "action_probe",
    "failure_basis",
    "evidence_scope",
)
_ROLE_CANDIDATE_FIELD = {
    PRODUCT_OPPORTUNITY_INVENTOR: "spontaneous_opportunity",
    CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: "architecture_transfer",
    FAILURE_EXPERIENCED_OPERATOR: "failure_earned_boundary",
}

_HOST_CANDIDATE_FIELDS = {
    "candidate_id",
    "candidate_fingerprint",
    "inventor_role",
    "partition_fingerprint",
    "frozen",
}

_ADVERSE_VALUES = {
    "adverse",
    "adverse_outcome",
    "adverse_result",
    "blocked",
    "failure",
    "failed",
    "incident",
    "mixed",
    "near_miss",
    "postmortem",
    "regression",
}

_GENERIC_PRODUCT_EVIDENCE_KINDS = {
    "bounded_user_request",
    "git_metadata",
    "repository_metadata",
    "test_metadata",
    "unknown_boundary",
    "workspace_git_metadata",
    "workspace_observation",
}

_PRODUCT_BEARING_CLAIM_FIELDS = (
    "claim",
    "excerpt",
    "observation",
    "observed_outcome",
    "observed_result",
    "result",
    "statement",
)

_BLINDED_CLAIM_IDENTITY_FIELDS = {
    "candidate_fingerprint",
    "candidate_id",
    "evidence_packet_id",
    "inventor_role",
    "item_id",
    "native_symbol_id",
    "partition_fingerprint",
    "repo_snapshot_id",
    "role",
    "source_id",
    "source_ids",
    "stable_identity",
}


class FrozenDict(Mapping):
    """A recursively immutable mapping used at every protocol boundary."""

    __slots__ = ("_data",)

    def __init__(self, value: Mapping[str, Any]):
        self._data = MappingProxyType(dict(value))

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"FrozenDict({self._data!r})"


def freeze(value: Any) -> Any:
    """Recursively freeze JSON-compatible values."""

    if isinstance(value, FrozenDict):
        return value
    if isinstance(value, Mapping):
        return FrozenDict({str(key): freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze(item) for item in value)
    return value


def thaw(value: Any) -> Any:
    """Return a detached, mutable, JSON-compatible copy of a frozen value."""

    if isinstance(value, Mapping):
        return {str(key): thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw(item) for item in value]
    return value


def fingerprint(value: Any) -> str:
    """Return a stable, domain-neutral SHA-256 fingerprint."""

    payload = json.dumps(
        thaw(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_clone(value: Any, field: str) -> Any:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return json.loads(encoded)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be JSON-compatible: {error}") from error


def _object(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    cloned = _json_clone(dict(value), field)
    if not isinstance(cloned, dict):
        raise ValueError(f"{field} must be an object")
    return cloned


def _exact_object(
    value: Any,
    field: str,
    required: Sequence[str],
    optional: Sequence[str] = (),
) -> Dict[str, Any]:
    row = _object(value, field)
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(required_set - set(row))
    extra = sorted(set(row) - allowed)
    if missing:
        raise ValueError(f"{field} missing required fields: {', '.join(missing)}")
    if extra:
        raise ValueError(f"{field} has forbidden fields: {', '.join(extra)}")
    return row


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _strings(
    value: Any,
    field: str,
    *,
    minimum: int = 0,
    unique: bool = True,
) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise ValueError(f"{field} must contain at least {minimum} strings")
    normalized = [_text(item, f"{field}[{index}]") for index, item in enumerate(value)]
    if unique and len(normalized) != len(set(normalized)):
        raise ValueError(f"{field} must contain unique strings")
    return normalized


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _normalize_evidence(value: Any, field: str) -> List[Dict[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field} must be an evidence array")
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        row = _object(item, f"{field}[{index}]")
        source_id = _text(row.get("source_id"), f"{field}[{index}].source_id")
        if source_id in seen:
            raise ValueError(f"{field} contains duplicate source_id: {source_id}")
        seen.add(source_id)
        row["source_id"] = source_id
        normalized.append(row)
    return normalized


def partition_cognition_evidence_bundle(
    bundle: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, Any]]:
    """Project a canonical evidence bundle into disjoint v3 role inputs.

    Local product facts are common because both a transferred mechanism and a
    failure-earned boundary must be adapted to the same target reality.  The raw
    request plus bounded knowledge/unknowns belong only to the opportunity
    inventor; prior opportunity and invention names are intentionally excluded.
    Only host-validated transfer mappings belong to the architecture analogist;
    raw revision-pinned excerpts alone cannot authorize it to invent a mapping.
    Only direct adverse outcome observations enter the failure operator's partition.
    """

    from palamedes_evidence_bundle import (
        direct_failure_outcome_id,
        validate_cognition_evidence_bundle,
    )

    validate_cognition_evidence_bundle(bundle)

    def as_source(item: Any, lane: str) -> Dict[str, Any]:
        row = _object(item, lane)
        source_id = _text(row.get("item_id"), f"{lane}.item_id")
        projected = _json_clone(row, lane)
        projected["source_id"] = source_id
        return projected

    common = [
        as_source(item, f"product_signals[{index}]")
        for index, item in enumerate(bundle.get("product_signals", []))
    ]

    request = _object(bundle.get("request"), "bundle.request")
    request_fingerprint = _text(
        request.get("request_fingerprint"), "bundle.request.request_fingerprint"
    )
    product_partition: List[Dict[str, Any]] = [
        {
            "source_id": f"request:{request_fingerprint}",
            "evidence_kind": "bounded_user_request",
            "user_request": _text(
                request.get("user_request"), "bundle.request.user_request"
            ),
            "epistemic_class": "direct_user_input",
            "delivery_authority_granted": False,
        }
    ]
    for lane in ("knowledge", "unknowns"):
        product_partition.extend(
            as_source(item, f"{lane}[{index}]")
            for index, item in enumerate(bundle.get(lane, []))
        )

    transfer = _object(
        bundle.get("cross_domain_transfer", {}), "bundle.cross_domain_transfer"
    )
    architecture_partition = [
        as_source(item, f"cross_domain_transfer.transfer_mappings[{index}]")
        for index, item in enumerate(transfer.get("transfer_mappings", []))
    ]

    direct_failure_ids = set(
        bundle.get("citation_allowlists", {}).get("direct_failure_ids", [])
    )
    failure_partition = []
    for index, item in enumerate(bundle.get("outcome_memory", [])):
        if not isinstance(item, Mapping):
            continue
        payload = item.get("payload")
        outcome_id = (
            str(payload.get("outcome_id", "")).strip()
            if isinstance(payload, Mapping)
            else ""
        )
        if (
            outcome_id not in direct_failure_ids
            or direct_failure_outcome_id(item) != outcome_id
        ):
            continue
        row = as_source(item, f"outcome_memory[{index}]")
        row["adverse"] = True
        row["outcome_status"] = str(payload.get("reported_outcome_status", "")).strip()
        failure_partition.append(row)

    constitution = {
        "authority_context": _json_clone(
            bundle.get("authority_context", {}), "bundle.authority_context"
        ),
        "mission_source_allowlist": list(
            bundle.get("citation_allowlists", {}).get("mission_source_ids", [])
        ),
        "planning_authority_granted": False,
        "delivery_authority_granted": False,
    }
    partitions = {
        PRODUCT_OPPORTUNITY_INVENTOR: product_partition,
        CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: architecture_partition,
        FAILURE_EXPERIENCED_OPERATOR: failure_partition,
    }
    # Validate uniqueness and the mandatory product slice before any provider
    # call. Return detached values so callers cannot mutate the bundle itself.
    normalized_common, normalized_partitions = _normalize_partitions(
        common, partitions
    )
    return normalized_common, normalized_partitions, constitution


def _normalize_partitions(
    common_evidence: Any, partitions: Any
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    common = _normalize_evidence(common_evidence, "common_evidence")
    if not isinstance(partitions, Mapping):
        raise ValueError("partitions must be an object keyed by inventor role")
    unknown = sorted(set(partitions) - set(INVENTOR_ROLES))
    missing = sorted(set(INVENTOR_ROLES) - set(partitions))
    if unknown:
        raise ValueError(f"partitions has unknown roles: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"partitions is missing roles: {', '.join(missing)}")

    normalized = {
        role: _normalize_evidence(partitions[role], f"partitions.{role}")
        for role in INVENTOR_ROLES
    }
    if not normalized[PRODUCT_OPPORTUNITY_INVENTOR]:
        raise ValueError(
            f"partitions.{PRODUCT_OPPORTUNITY_INVENTOR} must contain independent evidence"
        )

    owners: Dict[str, str] = {}
    for owner, records in [("common_evidence", common)] + [
        (f"partitions.{role}", normalized[role]) for role in INVENTOR_ROLES
    ]:
        for record in records:
            source_id = record["source_id"]
            prior = owners.get(source_id)
            if prior is not None:
                raise ValueError(
                    "source IDs must be globally disjoint; "
                    f"{source_id} appears in both {prior} and {owner}"
                )
            owners[source_id] = owner
    return common, normalized


def _normalized_marker(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _record_kind(record: Mapping[str, Any]) -> str:
    return _normalized_marker(record.get("kind") or record.get("evidence_kind"))


def _substantive_product_source_ids(
    records: Sequence[Mapping[str, Any]], constitution: Any
) -> set[str]:
    """Return host-citable local facts that are more than workspace metadata."""

    allowlist: Optional[set[str]] = None
    if isinstance(constitution, Mapping) and "mission_source_allowlist" in constitution:
        raw_allowlist = constitution.get("mission_source_allowlist")
        if not isinstance(raw_allowlist, list):
            raise ValueError("constitution.mission_source_allowlist must be an array")
        allowlist = {
            _text(item, "constitution.mission_source_allowlist[]")
            for item in raw_allowlist
        }

    substantive: set[str] = set()
    for record in records:
        source_id = _text(record.get("source_id"), "product evidence.source_id")
        if allowlist is not None and source_id not in allowlist:
            continue
        if _record_kind(record) in _GENERIC_PRODUCT_EVIDENCE_KINDS:
            continue
        authority = _normalized_marker(record.get("decision_authority"))
        if authority != "mission_citable":
            continue
        epistemic_class = _normalized_marker(record.get("epistemic_class"))
        if epistemic_class not in {
            "direct_observation",
            "direct_user_input",
            "host_verified",
        }:
            continue
        payload = record.get("payload")
        claim_containers = [record]
        if isinstance(payload, Mapping):
            claim_containers.append(payload)
        if not any(
            isinstance(container.get(field), str)
            and bool(container.get(field).strip())
            for container in claim_containers
            for field in _PRODUCT_BEARING_CLAIM_FIELDS
        ):
            continue
        substantive.add(source_id)
    return substantive


def _validated_architecture_mapping(
    record: Mapping[str, Any], field: str
) -> Optional[Dict[str, Any]]:
    """Project the immutable fields an analogist is permitted to copy."""

    from palamedes_architecture_transfer import (
        TRANSFER_CONTRACT_VERSION,
        verify_architecture_transfer_integrity,
    )

    if _record_kind(record) != "cross_domain_architecture_transfer":
        return None
    if _normalized_marker(record.get("decision_authority")) != "advisory":
        return None
    if _normalized_marker(record.get("epistemic_class")) != "hypothesis":
        return None
    if record.get("delivery_authority_granted") is not False:
        return None
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None
    try:
        # A public SHA digest is not provenance authentication.  This call also
        # requires the complete normalized v2 invariant set, source snapshot
        # bindings, target validation scope, and an unchanged host-produced
        # integrity record; a version/authority-only JSON projection abstains.
        verify_architecture_transfer_integrity(payload)
    except ValueError:
        return None
    if payload.get("transfer_contract_version") != TRANSFER_CONTRACT_VERSION:
        return None
    if payload.get("same_primary_job") is not False:
        return None
    if payload.get("source_outcome_is_target_forecast") is not False:
        return None
    if payload.get("authority") != "mechanism_candidate_only":
        return None
    for authority_field in (
        "decision_authority_granted",
        "design_authority_granted",
        "selection_authority_granted",
        "delivery_authority_granted",
        "code_reuse_authority_granted",
    ):
        if payload.get(authority_field) is not False:
            return None
    projected = {
        "source": _text(payload.get("source_domain"), f"{field}.payload.source_domain"),
        "pressure": _text(
            payload.get("source_pressure"), f"{field}.payload.source_pressure"
        ),
        "mechanism": _text(
            payload.get("source_pattern"), f"{field}.payload.source_pattern"
        ),
        "target": _text(
            payload.get("target_pressure"), f"{field}.payload.target_pressure"
        ),
        "adaptation": _text(
            payload.get("adaptation"), f"{field}.payload.adaptation"
        ),
    }
    limits = [
        _text(payload.get("transfer_limit"), f"{field}.payload.transfer_limit")
    ]
    for limit in _strings(
        payload.get("non_transferable_assumptions"),
        f"{field}.payload.non_transferable_assumptions",
    ):
        if limit not in limits:
            limits.append(limit)
    projected["limits"] = limits
    return projected


def _architecture_mapping_catalog(
    records: Sequence[Mapping[str, Any]], field: str
) -> Dict[str, Dict[str, Any]]:
    catalog: Dict[str, Dict[str, Any]] = {}
    for index, record in enumerate(records):
        mapping = _validated_architecture_mapping(record, f"{field}[{index}]")
        if mapping is not None:
            catalog[_text(record.get("source_id"), f"{field}[{index}].source_id")] = mapping
    return catalog


def _is_adverse_evidence(record: Mapping[str, Any]) -> bool:
    if record.get("adverse") is True or record.get("adverse_outcome") is True:
        return True
    for field in (
        "evidence_kind",
        "outcome",
        "status",
        "outcome_status",
        "reported_outcome_status",
        "outcome_type",
        "result",
    ):
        if _normalized_marker(record.get(field)) in _ADVERSE_VALUES:
            return True
    return False


def _normalize_business_effect(value: Any, field: str) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        (
            "revenue_or_value_effect",
            "causal_chain",
            "leading_indicator",
            "countervailing_risk",
        ),
    )
    row["revenue_or_value_effect"] = _text(
        row["revenue_or_value_effect"], f"{field}.revenue_or_value_effect"
    )
    row["causal_chain"] = _strings(
        row["causal_chain"], f"{field}.causal_chain", minimum=2
    )
    for name in ("leading_indicator", "countervailing_risk"):
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _normalize_lineage(
    value: Any,
    field: str,
    *,
    claim_source_ids: set[str],
    mechanism: str,
    behavior_change: str,
    business_effect: str,
) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        (
            "source_signal_ids",
            "signal",
            "latent_need",
            "mechanism",
            "behavior_change",
            "business_effect",
            "non_obvious_leap",
        ),
    )
    source_ids = _strings(
        row["source_signal_ids"], f"{field}.source_signal_ids", minimum=1
    )
    fabricated = sorted(set(source_ids) - claim_source_ids)
    if fabricated:
        raise ValueError(
            f"{field}.source_signal_ids cites unavailable source IDs: "
            + ", ".join(fabricated)
        )
    row["source_signal_ids"] = source_ids
    for name in (
        "signal",
        "latent_need",
        "mechanism",
        "behavior_change",
        "business_effect",
        "non_obvious_leap",
    ):
        row[name] = _text(row[name], f"{field}.{name}")
    if row["mechanism"] != mechanism:
        raise ValueError(f"{field}.mechanism must exactly trace product_mechanism")
    if row["behavior_change"] != behavior_change:
        raise ValueError(f"{field}.behavior_change must exactly trace behavior_change")
    if row["business_effect"] != business_effect:
        raise ValueError(
            f"{field}.business_effect must exactly trace business_effect.revenue_or_value_effect"
        )
    return row


def _normalize_second_order_effects(value: Any, field: str) -> List[Dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must contain at least one second-order effect")
    normalized: List[Dict[str, Any]] = []
    for index, item in enumerate(value):
        prefix = f"{field}[{index}]"
        row = _exact_object(
            item,
            prefix,
            (
                "stakeholder",
                "horizon",
                "valence",
                "first_order_effect",
                "second_order_effect",
                "feedback_or_externality",
                "early_signal",
            ),
        )
        for name in (
            "stakeholder",
            "horizon",
            "first_order_effect",
            "second_order_effect",
            "feedback_or_externality",
            "early_signal",
        ):
            row[name] = _text(row[name], f"{prefix}.{name}")
        valence = _text(row["valence"], f"{prefix}.valence")
        if valence not in {"benefit", "risk", "mixed"}:
            raise ValueError(f"{prefix}.valence must be benefit, risk, or mixed")
        row["valence"] = valence
        normalized.append(row)
    return normalized


def _normalize_operating_burden(value: Any, field: str) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        ("recurring_work", "owner", "cadence", "capacity_or_cost_limit", "failure_mode"),
    )
    for name in row:
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _normalize_authority(value: Any, field: str) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        (
            "decision_owner",
            "required_approvals",
            "prohibited_without_authority",
            "escalation_trigger",
        ),
    )
    row["decision_owner"] = _text(row["decision_owner"], f"{field}.decision_owner")
    row["required_approvals"] = _strings(
        row["required_approvals"], f"{field}.required_approvals", minimum=1
    )
    for name in ("prohibited_without_authority", "escalation_trigger"):
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _normalize_action_probe(value: Any, field: str) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        (
            "kind",
            "reversible",
            "terminal_output_kind",
            "intervention",
            "target_actor",
            "observation_window",
            "metric",
            "baseline_or_counterfactual",
            "falsifier",
            "rollback",
            "stop_condition",
            "authority_preconditions",
            "branches",
        ),
    )
    kind = _text(row["kind"], f"{field}.kind")
    if kind not in PROBE_KINDS:
        raise ValueError(f"{field}.kind is not an action probe")
    row["kind"] = kind
    if _boolean(row["reversible"], f"{field}.reversible") is not True:
        raise ValueError(f"{field}.reversible must be true")
    terminal = _text(row["terminal_output_kind"], f"{field}.terminal_output_kind")
    if terminal not in PROBE_TERMINAL_OUTPUTS:
        raise ValueError(f"{field} must end in observed or measured reality")
    row["terminal_output_kind"] = terminal
    for name in (
        "intervention",
        "target_actor",
        "observation_window",
        "metric",
        "baseline_or_counterfactual",
        "falsifier",
        "rollback",
        "stop_condition",
    ):
        row[name] = _text(row[name], f"{field}.{name}")
    row["authority_preconditions"] = _strings(
        row["authority_preconditions"],
        f"{field}.authority_preconditions",
        minimum=1,
    )
    branches = _exact_object(
        row["branches"],
        f"{field}.branches",
        ("if_supported", "if_refuted", "if_inconclusive"),
    )
    for name in branches:
        branches[name] = _text(branches[name], f"{field}.branches.{name}")
    row["branches"] = branches
    return row


def _normalize_failure_basis(
    value: Any,
    field: str,
    *,
    claim_source_ids: set[str],
    adverse_source_ids: set[str],
) -> Dict[str, Any]:
    row = _exact_object(
        value,
        field,
        (
            "basis_type",
            "source_ids",
            "lesson",
            "missing_viability_condition",
            "guardrail",
            "transfer_limit",
        ),
    )
    basis_type = _text(row["basis_type"], f"{field}.basis_type")
    if basis_type not in {"direct", "no_signal"}:
        raise ValueError(f"{field}.basis_type must be direct or no_signal")
    source_ids = _strings(row["source_ids"], f"{field}.source_ids")
    if basis_type == "no_signal" and source_ids:
        raise ValueError(f"{field}.no_signal must not cite source IDs")
    if basis_type == "direct":
        if not source_ids:
            raise ValueError(f"{field}.direct requires adverse source IDs")
        unavailable = sorted(set(source_ids) - claim_source_ids)
        if unavailable:
            raise ValueError(
                f"{field}.direct cites sources outside the candidate claim scope: "
                + ", ".join(unavailable)
            )
        non_adverse = sorted(set(source_ids) - adverse_source_ids)
        if non_adverse:
            raise ValueError(
                f"{field}.direct requires explicit adverse evidence: "
                + ", ".join(non_adverse)
            )
    row["basis_type"] = basis_type
    row["source_ids"] = source_ids
    for name in (
        "lesson",
        "missing_viability_condition",
        "guardrail",
        "transfer_limit",
    ):
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _normalize_role_specific(
    role: str,
    value: Any,
    field: str,
    *,
    claim_source_ids: set[str],
    exclusive_source_ids: set[str],
    failure_basis: Dict[str, Any],
    architecture_mappings: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    if role == PRODUCT_OPPORTUNITY_INVENTOR:
        row = _exact_object(
            value,
            field,
            (
                "unasked_opportunity",
                "why_signal_implies_it",
                "why_not_obvious",
                "existing_capability_reused",
                "product_boundary",
            ),
        )
        for name in row:
            row[name] = _text(row[name], f"{field}.{name}")
        return row

    if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
        row = _exact_object(
            value,
            field,
            ("source", "source_ids", "pressure", "mechanism", "target", "adaptation", "limits"),
        )
        for name in ("source", "pressure", "mechanism", "target", "adaptation"):
            row[name] = _text(row[name], f"{field}.{name}")
        source_ids = _strings(row["source_ids"], f"{field}.source_ids", minimum=1)
        unavailable = sorted(set(source_ids) - claim_source_ids)
        if unavailable:
            raise ValueError(
                f"{field}.source_ids cites unavailable sources: " + ", ".join(unavailable)
            )
        non_partition = sorted(set(source_ids) - exclusive_source_ids)
        if non_partition:
            raise ValueError(
                f"{field}.source_ids must come from the analogist's exclusive partition: "
                + ", ".join(non_partition)
            )
        if len(source_ids) != 1 or source_ids[0] not in architecture_mappings:
            raise ValueError(
                f"{field}.source_ids must select exactly one host-validated transfer mapping"
            )
        row["source_ids"] = source_ids
        row["limits"] = _strings(row["limits"], f"{field}.limits", minimum=1)
        mapping = architecture_mappings[source_ids[0]]
        for name in ("source", "pressure", "mechanism", "target", "adaptation"):
            if row[name] != mapping[name]:
                raise ValueError(
                    f"{field}.{name} must exactly copy the host-validated transfer mapping"
                )
        if row["limits"] != mapping["limits"]:
            raise ValueError(
                f"{field}.limits must exactly preserve the host-validated transfer limits"
            )
        return row

    row = _exact_object(
        value,
        field,
        (
            "source_failure_ids",
            "failed_assumption",
            "observed_adverse_outcome",
            "missing_viability_condition",
            "boundary",
            "guardrail",
            "transfer_limit",
        ),
    )
    source_ids = _strings(
        row["source_failure_ids"], f"{field}.source_failure_ids", minimum=1
    )
    if source_ids != failure_basis["source_ids"]:
        raise ValueError(
            f"{field}.source_failure_ids must exactly match failure_basis.source_ids"
        )
    non_archive = sorted(set(source_ids) - exclusive_source_ids)
    if non_archive:
        raise ValueError(
            f"{field}.source_failure_ids must come from the failure archive partition: "
            + ", ".join(non_archive)
        )
    row["source_failure_ids"] = source_ids
    for name in (
        "failed_assumption",
        "observed_adverse_outcome",
        "missing_viability_condition",
        "boundary",
        "guardrail",
        "transfer_limit",
    ):
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _normalize_candidate(
    value: Any,
    *,
    role: str,
    received_source_ids: List[str],
    exclusive_source_ids: set[str],
    adverse_source_ids: set[str],
    architecture_mappings: Mapping[str, Mapping[str, Any]],
    substantive_product_source_ids: set[str],
) -> Dict[str, Any]:
    role_field = _ROLE_CANDIDATE_FIELD[role]
    row = _exact_object(
        value,
        f"{role}.candidate",
        _COMMON_CANDIDATE_FIELDS + (role_field,),
    )
    if row["output_kind"] != "product_opportunity":
        raise ValueError(
            f"{role}.candidate.output_kind must be product_opportunity; "
            "generic code-review output is not admissible"
        )
    row["output_kind"] = "product_opportunity"
    for name in (
        "title",
        "opportunity_thesis",
        "beneficiary",
        "observed_signal",
        "product_mechanism",
        "behavior_change",
    ):
        row[name] = _text(row[name], f"{role}.candidate.{name}")

    scope_field = f"{role}.candidate.evidence_scope"
    scope = _exact_object(
        row["evidence_scope"],
        scope_field,
        ("received_source_ids", "claim_source_ids"),
    )
    received = _strings(
        scope["received_source_ids"], f"{scope_field}.received_source_ids"
    )
    if received != received_source_ids:
        raise ValueError(
            f"{scope_field}.received_source_ids must exactly match the host-assigned source subset"
        )
    claims = _strings(
        scope["claim_source_ids"], f"{scope_field}.claim_source_ids", minimum=1
    )
    fabricated = sorted(set(claims) - set(received_source_ids))
    if fabricated:
        raise ValueError(
            f"{scope_field}.claim_source_ids cites fabricated source IDs: "
            + ", ".join(fabricated)
        )
    if not set(claims) & substantive_product_source_ids:
        raise ValueError(
            f"{scope_field}.claim_source_ids must include substantive non-generic "
            "mission-citable product evidence"
        )
    scope["received_source_ids"] = received
    scope["claim_source_ids"] = claims
    row["evidence_scope"] = scope

    business = _normalize_business_effect(
        row["business_effect"], f"{role}.candidate.business_effect"
    )
    row["business_effect"] = business
    row["product_opportunity_lineage"] = _normalize_lineage(
        row["product_opportunity_lineage"],
        f"{role}.candidate.product_opportunity_lineage",
        claim_source_ids=set(claims),
        mechanism=row["product_mechanism"],
        behavior_change=row["behavior_change"],
        business_effect=business["revenue_or_value_effect"],
    )
    row["second_order_effects"] = _normalize_second_order_effects(
        row["second_order_effects"], f"{role}.candidate.second_order_effects"
    )
    row["operating_burden"] = _normalize_operating_burden(
        row["operating_burden"], f"{role}.candidate.operating_burden"
    )
    row["authority"] = _normalize_authority(
        row["authority"], f"{role}.candidate.authority"
    )
    row["action_probe"] = _normalize_action_probe(
        row["action_probe"], f"{role}.candidate.action_probe"
    )
    failure_basis = _normalize_failure_basis(
        row["failure_basis"],
        f"{role}.candidate.failure_basis",
        claim_source_ids=set(claims),
        adverse_source_ids=adverse_source_ids,
    )
    if role == FAILURE_EXPERIENCED_OPERATOR and failure_basis["basis_type"] != "direct":
        raise ValueError(
            "failure_experienced_operator may emit a candidate only with direct adverse evidence"
        )
    row["failure_basis"] = failure_basis
    row[role_field] = _normalize_role_specific(
        role,
        row[role_field],
        f"{role}.candidate.{role_field}",
        claim_source_ids=set(claims),
        exclusive_source_ids=exclusive_source_ids,
        failure_basis=failure_basis,
        architecture_mappings=architecture_mappings,
    )
    if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
        transfer = row[role_field]
        if row["product_mechanism"] != transfer["adaptation"]:
            raise ValueError(
                f"{role}.candidate.product_mechanism must exactly copy "
                "architecture_transfer.adaptation"
            )
        if row["failure_basis"]["transfer_limit"] != transfer["limits"][0]:
            raise ValueError(
                f"{role}.candidate.failure_basis.transfer_limit must preserve "
                "the host-validated primary transfer limit"
            )
    return row


def _normalize_abstention(value: Any, field: str) -> Dict[str, Any]:
    row = _exact_object(value, field, ("reason", "missing_evidence", "wake_condition"))
    for name in row:
        row[name] = _text(row[name], f"{field}.{name}")
    return row


def _candidate_contract_text(role: str) -> str:
    role_requirement = {
        PRODUCT_OPPORTUNITY_INVENTOR: (
            "Add spontaneous_opportunity with exactly: unasked_opportunity, "
            "why_signal_implies_it, why_not_obvious, existing_capability_reused, "
            "product_boundary. Discover a product/business move the requester did not name."
        ),
        CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: (
            "Add architecture_transfer with exactly: source, source_ids, pressure, "
            "mechanism, target, adaptation, limits. This is a causal "
            "source→pressure→mechanism→target→adaptation→limits transfer, not a list "
            "of libraries or a claim that two products look alike. Select exactly one "
            "exclusive host-validated mapping source_id, then copy source, pressure, "
            "mechanism, target, adaptation, and the complete ordered limits array from "
            "that mapping without paraphrase. product_mechanism must exactly copy "
            "architecture_transfer.adaptation and failure_basis.transfer_limit must "
            "exactly copy its first limit."
        ),
        FAILURE_EXPERIENCED_OPERATOR: (
            "Add failure_earned_boundary with exactly: source_failure_ids, "
            "failed_assumption, observed_adverse_outcome, missing_viability_condition, "
            "boundary, guardrail, transfer_limit. A candidate requires failure_basis.direct."
        ),
    }[role]
    return f"""
Return exactly one of these envelopes:
  {{"status":"candidate","candidate":{{...}}}}
  {{"status":"abstain","abstention":{{"reason":"...","missing_evidence":"...","wake_condition":"..."}}}}

A candidate must have output_kind="product_opportunity" and exactly these common
fields: {json.dumps(_COMMON_CANDIDATE_FIELDS)}. Do not issue candidate_id or a
fingerprint; the host owns identity. {role_requirement}

business_effect has exactly revenue_or_value_effect, causal_chain (at least two
steps), leading_indicator, countervailing_risk. product_opportunity_lineage has
exactly source_signal_ids, signal, latent_need, mechanism, behavior_change,
business_effect, non_obvious_leap. lineage.mechanism must exactly copy
candidate.product_mechanism; lineage.behavior_change must exactly copy
candidate.behavior_change; lineage.business_effect must be non-empty and exactly
copy candidate.business_effect.revenue_or_value_effect. second_order_effects is
non-empty and each entry has
stakeholder, horizon, valence (benefit|risk|mixed), first_order_effect,
second_order_effect, feedback_or_externality, early_signal.

operating_burden has exactly recurring_work, owner, cadence,
capacity_or_cost_limit, failure_mode. authority has exactly decision_owner,
required_approvals (non-empty array), prohibited_without_authority,
escalation_trigger.

action_probe has exactly kind, reversible=true, terminal_output_kind,
intervention, target_actor, observation_window, metric,
baseline_or_counterfactual, falsifier, rollback, stop_condition,
authority_preconditions (non-empty array), and branches. branches has exactly
if_supported, if_refuted, if_inconclusive. The probe must change or expose reality;
do not return a code review, planning workshop, or another meta-review. kind must
be exactly one of {json.dumps(sorted(PROBE_KINDS))}; for a mock or concept shown
to people use behavioral_exposure, never invent a descriptive enum.
terminal_output_kind must be exactly one of
{json.dumps(sorted(PROBE_TERMINAL_OUTPUTS))}; a report/document is not terminal
reality, so a cohort concept exposure ends in observed_actor_response.

failure_basis has exactly basis_type (direct|no_signal), source_ids, lesson,
missing_viability_condition, guardrail, transfer_limit. direct may cite only an
explicit adverse source in the supplied packet; no_signal must use [].
evidence_scope has exactly received_source_ids and claim_source_ids. Copy
received_source_ids from allowed_source_ids in the same order. claim_source_ids
must be a non-empty subset. Never fabricate a source ID. A source ID certifies
only the exact host-supplied source payload; it does not turn observed_signal or
any other model-authored interpretation into an observed fact.
""".strip()


def _inventor_prompt(role: str, packet: Dict[str, Any]) -> str:
    opening = {
        PRODUCT_OPPORTUNITY_INVENTOR: (
            "Infer a spontaneous, unasked product or business opportunity from the "
            "bounded signals. Trace an underused capability or behavioral gap through "
            "a product mechanism to durable user value and a plausible business effect. "
            "Do not review code quality."
        ),
        CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: (
            "Use an unrelated source pattern only for its causal architecture. Explain "
            "the source pressure, transferable mechanism, target adaptation, and hard "
            "limits. Do not recommend an open source project merely because its topic matches."
        ),
        FAILURE_EXPERIENCED_OPERATOR: (
            "Derive a boundary that is visible because a prior attempt had an explicit "
            "adverse outcome. Do not simulate experience or convert generic risk into a "
            "failure-earned lesson."
        ),
    }[role]
    return (
        f"ROLE_ASSIGNMENT: {role}\n\n{opening}\n\n"
        "You are in an isolated generation call. No rival candidate exists in your "
        "visible context. Use only HOST_PACKET_JSON.\n\n"
        + _candidate_contract_text(role)
        + "\n\nHOST_PACKET_JSON:\n"
        + json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    )


def _forced_failure_abstention(received_source_ids: List[str]) -> Dict[str, Any]:
    payload = {
        "role": FAILURE_EXPERIENCED_OPERATOR,
        "reason_code": "no_adverse_evidence",
        "reason": "No explicitly adverse outcome is present in this role's assigned evidence.",
        "missing_evidence": "A failed, blocked, mixed, near-miss, or adverse observed outcome.",
        "wake_condition": "Add a bounded adverse record with a stable source_id and observed outcome status.",
        "failure_basis": {
            "basis_type": "no_signal",
            "source_ids": [],
            "lesson": "No failure-earned lesson may be claimed from success or neutral context.",
            "missing_viability_condition": "Unknown until an adverse record exists.",
            "guardrail": "Abstain instead of fabricating operational experience.",
            "transfer_limit": "This abstention says nothing about whether the opportunity itself is viable.",
        },
        "received_source_ids": list(received_source_ids),
    }
    payload["abstention_id"] = "abstention-" + fingerprint(payload).split(":", 1)[1][:16]
    return payload


def _forced_architecture_abstention(received_source_ids: List[str]) -> Dict[str, Any]:
    payload = {
        "role": CROSS_DOMAIN_ARCHITECTURE_ANALOGIST,
        "reason_code": "no_validated_cross_domain_evidence",
        "reason": (
            "No revision-pinned, host-validated cross-domain architecture evidence "
            "is present in this role's assigned partition."
        ),
        "missing_evidence": (
            "A reference-only source packet and a bounded source-to-target transfer "
            "with explicit differences and limits."
        ),
        "wake_condition": (
            "Add a host-validated cross-domain transfer mapping with stable source IDs."
        ),
        "received_source_ids": list(received_source_ids),
    }
    payload["abstention_id"] = "abstention-" + fingerprint(payload).split(":", 1)[1][:16]
    return payload


def _forced_product_grounding_abstention(
    role: str, received_source_ids: List[str]
) -> Dict[str, Any]:
    payload = {
        "role": role,
        "reason_code": "no_substantive_product_evidence",
        "reason": (
            "Only generic request, workspace, repository, test, or unknown metadata "
            "is available; it cannot ground a product opportunity."
        ),
        "missing_evidence": (
            "A non-generic mission-citable product observation or host-verified "
            "capability, gap, document claim, or adverse outcome."
        ),
        "wake_condition": (
            "Add a bounded host-citable product fact beyond workspace or Git metadata."
        ),
        "received_source_ids": list(received_source_ids),
    }
    payload["abstention_id"] = (
        "abstention-" + fingerprint(payload).split(":", 1)[1][:16]
    )
    return payload


def _ask_object(ask: Callable[[str, str], Any], role: str, prompt: str) -> Dict[str, Any]:
    return _object(ask(role, prompt), f"response from {role}")


def _sanitize_candidate_content(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    content = {
        key: thaw(value)
        for key, value in candidate.items()
        if key not in _HOST_CANDIDATE_FIELDS
    }
    scope = content.pop("evidence_scope", None)
    if isinstance(scope, dict):
        content["evidence_summary"] = {
            "received_source_count": len(scope.get("received_source_ids", [])),
            "claim_source_count": len(scope.get("claim_source_ids", [])),
        }
    lineage = content.get("product_opportunity_lineage")
    if isinstance(lineage, dict):
        source_ids = lineage.pop("source_signal_ids", [])
        lineage["source_signal_count"] = len(source_ids)
    failure = content.get("failure_basis")
    if isinstance(failure, dict):
        source_ids = failure.pop("source_ids", [])
        failure["source_count"] = len(source_ids)
    architecture = content.get("architecture_transfer")
    if isinstance(architecture, dict):
        source_ids = architecture.pop("source_ids", [])
        architecture["source_count"] = len(source_ids)
    boundary = content.get("failure_earned_boundary")
    if isinstance(boundary, dict):
        source_ids = boundary.pop("source_failure_ids", [])
        boundary["source_failure_count"] = len(source_ids)
    return content


def _sanitize_host_claim_value(value: Any) -> Any:
    """Remove stable identities while preserving exact host-owned claim substance."""

    if isinstance(value, Mapping):
        sanitized = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            if (
                key in _BLINDED_CLAIM_IDENTITY_FIELDS
                or key.endswith("_id")
                or key.endswith("_ids")
                or key.endswith("_fingerprint")
            ):
                continue
            sanitized[key] = _sanitize_host_claim_value(item)
        return sanitized
    if isinstance(value, (list, tuple)):
        return [_sanitize_host_claim_value(item) for item in value]
    return _json_clone(value, "host claim")


def _sanitize_host_claims(
    candidate: Mapping[str, Any], evidence_by_source_id: Mapping[str, Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Expose cited host evidence to a critic under opaque, origin-free references."""

    scope = candidate.get("evidence_scope")
    if not isinstance(scope, Mapping):
        raise ValueError("frozen candidate evidence_scope is malformed")
    claim_source_ids = scope.get("claim_source_ids")
    if not isinstance(claim_source_ids, (list, tuple)):
        raise ValueError("frozen candidate claim_source_ids is malformed")
    claims: List[Dict[str, Any]] = []
    for index, source_id in enumerate(claim_source_ids, start=1):
        record = evidence_by_source_id.get(str(source_id))
        if record is None:
            raise ValueError("frozen candidate cites evidence missing from host custody")
        claims.append(
            {
                "claim_ref": f"claim-{index}",
                "custody": "host_supplied_evidence",
                "evidence_kind": _record_kind(record) or "unspecified",
                "epistemic_class": _normalized_marker(
                    record.get("epistemic_class")
                )
                or "unspecified",
                "decision_authority": _normalized_marker(
                    record.get("decision_authority")
                )
                or "unspecified",
                "status": _normalized_marker(record.get("status")) or "unspecified",
                "claim_payload": _sanitize_host_claim_value(record),
            }
        )
    return claims


def _normalize_critique(
    value: Any, *, review_subject_id: str, candidate_id: str, candidate_fingerprint: str
) -> Dict[str, Any]:
    field = f"critique for {review_subject_id}"
    row = _exact_object(
        value,
        field,
        (
            "review_subject_id",
            "verdict",
            "disqualification_reasons",
            "constitutional_tension",
            "causal_weakness",
            "business_viability_attack",
            "second_order_risk",
            "operating_failure_mode",
            "probe_weakness",
            "strongest_surviving_case",
        ),
    )
    if row["review_subject_id"] != review_subject_id:
        raise ValueError(f"{field}.review_subject_id must match the host-issued blind subject")
    verdict = _text(row["verdict"], f"{field}.verdict")
    if verdict not in {"qualified", "disqualified"}:
        raise ValueError(f"{field}.verdict must be qualified or disqualified")
    reasons = _strings(row["disqualification_reasons"], f"{field}.disqualification_reasons")
    if verdict == "disqualified" and not reasons:
        raise ValueError(f"{field} requires a reason when disqualified")
    if verdict == "qualified" and reasons:
        raise ValueError(f"{field} cannot attach disqualification reasons to a qualified candidate")
    row["verdict"] = verdict
    row["disqualification_reasons"] = reasons
    for name in (
        "constitutional_tension",
        "causal_weakness",
        "business_viability_attack",
        "second_order_risk",
        "operating_failure_mode",
        "probe_weakness",
        "strongest_surviving_case",
    ):
        row[name] = _text(row[name], f"{field}.{name}")
    critique_payload = {
        "candidate_id": candidate_id,
        "candidate_fingerprint": candidate_fingerprint,
        "blinded": True,
        **row,
    }
    critique_fp = fingerprint(critique_payload)
    return {
        "critique_id": "critique-" + critique_fp.split(":", 1)[1][:16],
        "critique_fingerprint": critique_fp,
        **critique_payload,
    }


def _adversary_prompt(
    *,
    constitution: Any,
    review_subject_id: str,
    sanitized_content: Dict[str, Any],
    sanitized_host_claims: List[Dict[str, Any]],
) -> str:
    packet = {
        "constitution": constitution,
        "review_subject_id": review_subject_id,
        "candidate": sanitized_content,
        "host_claims": sanitized_host_claims,
    }
    return f"""ROLE: origin-blinded product adversary

Review exactly one frozen candidate. Author identity, inventor assignment, raw
evidence IDs, persuasive history, and every rival candidate are withheld. Do not
guess them and do not rewrite the candidate. host_claims contains sanitized exact
host-owned payloads cited by this candidate under fresh opaque references. Treat
candidate wording as inference, not observation: explicitly judge whether those
host claims support observed_signal, lineage, mechanism, and causal business effect.

Return exactly these fields: review_subject_id, verdict (qualified|disqualified),
disqualification_reasons (use [] when qualified), constitutional_tension,
causal_weakness, business_viability_attack, second_order_risk,
operating_failure_mode, probe_weakness, strongest_surviving_case.

Disqualify only for a fatal grounding, authority, harm, causal, or testability
failure; ordinary uncertainty belongs in the attacks and may still qualify.

HOST_PACKET_JSON:
{json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}"""


_DECISION_DETAIL_FIELDS = {
    "commit": ("commitment_scope", "review_trigger"),
    "bounded_exploration": (
        "exploration_budget",
        "expires_when",
        "learning_objective",
        "stop_condition",
    ),
    "discriminating_probe": (
        "ambiguity",
        "probe",
        "metric",
        "budget",
        "maximum_harm",
        "stop_condition",
    ),
    "defer": ("missing_condition", "wake_trigger", "review_at"),
}


def _normalize_selector_decision(
    value: Any,
    *,
    known_candidate_ids: set[str],
    qualified_candidate_ids: set[str],
) -> Dict[str, Any]:
    row = _exact_object(
        value,
        "selector decision",
        (
            "mode",
            "selected_candidate_ids",
            "rationale",
            "unresolved_conflicts",
            "decision_details",
        ),
    )
    mode = _text(row["mode"], "selector decision.mode")
    if mode not in SELECTOR_MODES:
        raise ValueError("selector decision.mode is not recognized")
    selected = _strings(
        row["selected_candidate_ids"], "selector decision.selected_candidate_ids"
    )
    unknown = sorted(set(selected) - known_candidate_ids)
    if unknown:
        raise ValueError(
            "selector selected unknown candidate IDs: " + ", ".join(unknown)
        )
    disqualified = sorted(set(selected) - qualified_candidate_ids)
    if disqualified:
        raise ValueError(
            "disqualified candidate cannot be selected: " + ", ".join(disqualified)
        )
    row["mode"] = mode
    row["selected_candidate_ids"] = selected
    row["rationale"] = _text(row["rationale"], "selector decision.rationale")
    row["unresolved_conflicts"] = _strings(
        row["unresolved_conflicts"], "selector decision.unresolved_conflicts"
    )
    details = _exact_object(
        row["decision_details"],
        "selector decision.decision_details",
        _DECISION_DETAIL_FIELDS[mode],
    )
    for name in details:
        details[name] = _text(details[name], f"selector decision.decision_details.{name}")
    row["decision_details"] = details

    if mode == "commit" and len(selected) != 1:
        raise ValueError("commit must select exactly one qualified candidate")
    if mode == "bounded_exploration":
        if not selected:
            raise ValueError("bounded_exploration must select at least one qualified candidate")
        if len(selected) >= len(qualified_candidate_ids):
            raise ValueError(
                "bounded_exploration must select a strict subset of qualified candidates"
            )
    if mode == "discriminating_probe" and len(selected) < 2:
        raise ValueError("discriminating_probe must retain at least two qualified candidates")
    if mode == "defer" and selected:
        raise ValueError("defer must not select a candidate")
    return row


def _selector_prompt(
    *, constitution: Any, candidates: List[Dict[str, Any]], critiques: List[Dict[str, Any]]
) -> str:
    packet = {
        "constitution": constitution,
        "sanitized_frozen_candidates": candidates,
        "sanitized_blinded_critiques": critiques,
    }
    return f"""ROLE: product cognition selector

Choose among four modes using only the constitution, sanitized frozen candidates,
and sanitized blinded critiques in HOST_PACKET_JSON. You cannot see raw evidence,
partitions, inventor identities, generation history, or unsanitized candidate data.
Do not rewrite, patch, merge, or issue a candidate. The host alone may issue a draft.

These modes govern the next bounded epistemic action, not a production build.
commit means the host may copy exactly one qualified candidate's already-bounded
action_probe into a human-reviewable draft; it does not approve the product thesis,
price, reward, launch, implementation, or delivery. Do not demand the evidence that
the candidate's own reversible probe is specifically designed to obtain. Instead ask
whether existing evidence justifies running that probe under its authority
preconditions, falsifier, stop condition, and rollback. Specialized approvals may
remain unresolved on the draft and are not satisfied by this selection. Defer only
when even the proposed epistemic action is unsafe, non-discriminating, ungrounded, or
not worth its bounded cost.

Return exactly: mode, selected_candidate_ids, rationale, unresolved_conflicts, and
decision_details. Modes and exact decision_details fields are:
  commit: commitment_scope, review_trigger
  bounded_exploration: exploration_budget, expires_when, learning_objective, stop_condition
  discriminating_probe: ambiguity, probe, metric, budget, maximum_harm, stop_condition
  defer: missing_condition, wake_trigger, review_at

commit selects exactly one qualified candidate. bounded_exploration selects a strict
non-empty subset of qualified candidates. discriminating_probe selects at least two
qualified candidates. defer selects none. Never select a disqualified candidate.

HOST_PACKET_JSON:
{json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}"""


def _host_issue(
    decision: Dict[str, Any], candidates_by_id: Dict[str, Mapping[str, Any]]
) -> Dict[str, Any]:
    selected = decision["selected_candidate_ids"]
    copied = [thaw(candidates_by_id[candidate_id]) for candidate_id in selected]
    base: Dict[str, Any] = {
        "issued_by": "product_cognition_host",
        "mode": decision["mode"],
        "selected_candidate_ids": list(selected),
        "decision_details": _json_clone(decision["decision_details"], "decision_details"),
    }
    if decision["mode"] == "commit":
        base["result_kind"] = "draft"
        base["draft"] = copied[0]
    elif decision["mode"] == "bounded_exploration":
        base["result_kind"] = "bounded_exploration"
        base["exploration_candidates"] = copied
        base["bounds"] = _json_clone(decision["decision_details"], "decision_details")
    elif decision["mode"] == "discriminating_probe":
        base["result_kind"] = "discriminating_probe"
        base["competing_candidates"] = copied
        base["probe"] = _json_clone(decision["decision_details"], "decision_details")
    else:
        base["result_kind"] = "defer"
        base["defer"] = _json_clone(decision["decision_details"], "decision_details")
    base["issue_fingerprint"] = fingerprint(base)
    return base


def run_partitioned_product_cognition(
    *,
    ask: Callable[[str, str], Dict[str, Any]],
    common_evidence: Any,
    partitions: Mapping[str, Any],
    constitution: Optional[Any] = None,
) -> FrozenDict:
    """Run independent product cognition, blind review, and governed selection.

    ``common_evidence`` and every partition are arrays of JSON objects with a
    globally unique ``source_id``. ``partitions`` must contain exactly the three
    keys in :data:`INVENTOR_ROLES`; the product partition must be non-empty.
    Architecture and failure partitions may be empty; in either case the host
    records an abstention instead of asking a model to invent missing evidence. A failure record is
    adverse only when its structured status/kind explicitly says so (or it has
    ``adverse: true``); descriptive prose alone never grants experiential authority.

    The returned value is recursively immutable.  The selector never receives a
    mutable candidate object, and its response is treated only as a decision.  The
    host creates the final draft/exploration result by copying already-frozen
    candidate records after validating the selected IDs and critique verdicts.
    """

    if not callable(ask):
        raise ValueError("ask must be callable")
    common, exclusive = _normalize_partitions(common_evidence, partitions)
    constitution_payload = (
        None if constitution is None else _json_clone(constitution, "constitution")
    )

    common_source_ids = [row["source_id"] for row in common]
    evidence_by_source_id = {
        row["source_id"]: row
        for row in common
        + [record for role in INVENTOR_ROLES for record in exclusive[role]]
    }
    generated: List[Dict[str, Any]] = []
    abstentions: List[Dict[str, Any]] = []
    partition_audit: List[Dict[str, Any]] = []

    # No response is added to any later inventor packet.  Candidate records are
    # normalized and fingerprinted immediately, then all are collectively frozen
    # before the first adversarial call.
    for role in INVENTOR_ROLES:
        exclusive_records = exclusive[role]
        received_records = common + exclusive_records
        received_source_ids = [row["source_id"] for row in received_records]
        adverse_source_ids = {
            row["source_id"] for row in received_records if _is_adverse_evidence(row)
        }
        failure_archive_adverse_source_ids = {
            row["source_id"] for row in exclusive_records if _is_adverse_evidence(row)
        }
        substantive_product_source_ids = _substantive_product_source_ids(
            received_records, constitution_payload
        )
        architecture_mappings = _architecture_mapping_catalog(
            exclusive_records, f"partitions.{role}"
        )
        partition_payload = {
            "role": role,
            "common_source_ids": common_source_ids,
            "exclusive_source_ids": [row["source_id"] for row in exclusive_records],
            "evidence": received_records,
        }
        partition_fp = fingerprint(partition_payload)
        audit_row: Dict[str, Any] = {
            "role": role,
            "partition_fingerprint": partition_fp,
            "common_source_ids": list(common_source_ids),
            "exclusive_source_ids": [row["source_id"] for row in exclusive_records],
        }

        if (
            role == PRODUCT_OPPORTUNITY_INVENTOR
            and not substantive_product_source_ids
        ):
            abstention = _forced_product_grounding_abstention(
                role, received_source_ids
            )
            abstentions.append(abstention)
            audit_row["outcome_id"] = abstention["abstention_id"]
            audit_row["outcome_kind"] = "host_forced_abstention"
            partition_audit.append(audit_row)
            continue

        if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST and not architecture_mappings:
            abstention = _forced_architecture_abstention(received_source_ids)
            abstentions.append(abstention)
            audit_row["outcome_id"] = abstention["abstention_id"]
            audit_row["outcome_kind"] = "host_forced_abstention"
            partition_audit.append(audit_row)
            continue

        if role == FAILURE_EXPERIENCED_OPERATOR and not failure_archive_adverse_source_ids:
            abstention = _forced_failure_abstention(received_source_ids)
            abstentions.append(abstention)
            audit_row["outcome_id"] = abstention["abstention_id"]
            audit_row["outcome_kind"] = "host_forced_abstention"
            partition_audit.append(audit_row)
            continue

        if not substantive_product_source_ids:
            abstention = _forced_product_grounding_abstention(
                role, received_source_ids
            )
            abstentions.append(abstention)
            audit_row["outcome_id"] = abstention["abstention_id"]
            audit_row["outcome_kind"] = "host_forced_abstention"
            partition_audit.append(audit_row)
            continue

        packet = {
            "protocol_version": COGNITION_VERSION,
            "constitution": constitution_payload,
            "common_evidence": common,
            "exclusive_evidence": exclusive_records,
            "allowed_source_ids": received_source_ids,
            "adverse_source_ids": sorted(
                failure_archive_adverse_source_ids
                if role == FAILURE_EXPERIENCED_OPERATOR
                else adverse_source_ids
            ),
            "partition_fingerprint": partition_fp,
            "rival_candidates_visible": False,
        }
        response = _ask_object(ask, role, _inventor_prompt(role, packet))
        status = _text(response.get("status"), f"response from {role}.status")
        if status == "abstain":
            envelope = _exact_object(
                response, f"response from {role}", ("status", "abstention")
            )
            abstention_content = _normalize_abstention(
                envelope["abstention"], f"response from {role}.abstention"
            )
            abstention_payload = {
                "role": role,
                "reason_code": "inventor_abstention",
                **abstention_content,
                "received_source_ids": received_source_ids,
            }
            abstention_payload["abstention_id"] = (
                "abstention-" + fingerprint(abstention_payload).split(":", 1)[1][:16]
            )
            abstentions.append(abstention_payload)
            audit_row["outcome_id"] = abstention_payload["abstention_id"]
            audit_row["outcome_kind"] = "inventor_abstention"
            partition_audit.append(audit_row)
            continue
        if status != "candidate":
            raise ValueError(f"response from {role}.status must be candidate or abstain")
        envelope = _exact_object(
            response, f"response from {role}", ("status", "candidate")
        )
        candidate = _normalize_candidate(
            envelope["candidate"],
            role=role,
            received_source_ids=received_source_ids,
            exclusive_source_ids={row["source_id"] for row in exclusive_records},
            adverse_source_ids=adverse_source_ids,
            architecture_mappings=architecture_mappings,
            substantive_product_source_ids=substantive_product_source_ids,
        )
        candidate_fp = fingerprint(
            {
                "protocol_version": COGNITION_VERSION,
                "inventor_role": role,
                "partition_fingerprint": partition_fp,
                "candidate": candidate,
            }
        )
        candidate_record = {
            "candidate_id": "candidate-" + candidate_fp.split(":", 1)[1][:16],
            "candidate_fingerprint": candidate_fp,
            "inventor_role": role,
            "partition_fingerprint": partition_fp,
            "frozen": True,
            **candidate,
        }
        if any(
            existing["candidate_id"] == candidate_record["candidate_id"]
            for existing in generated
        ):
            raise ValueError("host-issued candidate ID collision")
        generated.append(candidate_record)
        audit_row["outcome_id"] = candidate_record["candidate_id"]
        audit_row["outcome_kind"] = "frozen_candidate"
        partition_audit.append(audit_row)

    frozen_candidates: Tuple[FrozenDict, ...] = tuple(freeze(row) for row in generated)
    frozen_set_fp = fingerprint([row["candidate_fingerprint"] for row in frozen_candidates])

    critiques: List[Dict[str, Any]] = []
    for candidate in frozen_candidates:
        review_subject_id = (
            "blind-subject-"
            + hashlib.sha256(
                ("product-cognition-v3:" + candidate["candidate_fingerprint"]).encode("utf-8")
            ).hexdigest()[:16]
        )
        sanitized_content = _sanitize_candidate_content(candidate)
        sanitized_host_claims = _sanitize_host_claims(
            candidate, evidence_by_source_id
        )
        response = _ask_object(
            ask,
            BLINDED_ADVERSARY_ROLE,
            _adversary_prompt(
                constitution=constitution_payload,
                review_subject_id=review_subject_id,
                sanitized_content=sanitized_content,
                sanitized_host_claims=sanitized_host_claims,
            ),
        )
        critique = _normalize_critique(
            response,
            review_subject_id=review_subject_id,
            candidate_id=candidate["candidate_id"],
            candidate_fingerprint=candidate["candidate_fingerprint"],
        )
        critiques.append(critique)
    frozen_critiques: Tuple[FrozenDict, ...] = tuple(freeze(row) for row in critiques)
    critique_set_fp = fingerprint(
        [row["critique_fingerprint"] for row in frozen_critiques]
    )

    selector_candidates = [
        {
            "candidate_id": candidate["candidate_id"],
            "candidate_fingerprint": candidate["candidate_fingerprint"],
            "frozen": True,
            "content": _sanitize_candidate_content(candidate),
        }
        for candidate in frozen_candidates
    ]
    selector_critiques = [
        {
            key: thaw(value)
            for key, value in critique.items()
            if key not in {"review_subject_id"}
        }
        for critique in frozen_critiques
    ]
    known_ids = {row["candidate_id"] for row in frozen_candidates}
    qualified_ids = {
        row["candidate_id"]
        for row in frozen_critiques
        if row["verdict"] == "qualified"
    }
    if frozen_candidates:
        selector_response = _ask_object(
            ask,
            SELECTOR_ROLE,
            _selector_prompt(
                constitution=constitution_payload,
                candidates=selector_candidates,
                critiques=selector_critiques,
            ),
        )
        decision = _normalize_selector_decision(
            selector_response,
            known_candidate_ids=known_ids,
            qualified_candidate_ids=qualified_ids,
        )
        selector_called = True
    else:
        decision = {
            "mode": "defer",
            "selected_candidate_ids": [],
            "rationale": (
                "The host admitted no grounded candidate, so no model selection "
                "or product-opportunity commitment is permitted."
            ),
            "unresolved_conflicts": [
                "Substantive non-generic product evidence is unavailable."
            ],
            "decision_details": {
                "missing_condition": (
                    "At least one qualified candidate grounded in substantive "
                    "mission-citable product evidence."
                ),
                "wake_trigger": (
                    "A bounded host-citable product fact enters an inventor partition."
                ),
                "review_at": "At the next evidence refresh.",
            },
        }
        selector_called = False

    # Recompute after selection as a tripwire even though the selector only saw a
    # serialized sanitized copy and the records themselves are immutable.
    if fingerprint([row["candidate_fingerprint"] for row in frozen_candidates]) != frozen_set_fp:
        raise ValueError("frozen candidates changed during selection")
    decision_record = {
        "selection_fingerprint": fingerprint(
            {
                "candidate_set_fingerprint": frozen_set_fp,
                "critique_set_fingerprint": critique_set_fp,
                "decision": decision,
            }
        ),
        "candidate_set_fingerprint": frozen_set_fp,
        "critique_set_fingerprint": critique_set_fp,
        **decision,
    }
    candidates_by_id = {row["candidate_id"]: row for row in frozen_candidates}
    issued = _host_issue(decision, candidates_by_id)

    result = {
        "protocol_version": COGNITION_VERSION,
        "frozen_candidates": list(frozen_candidates),
        "abstentions": abstentions,
        "blinded_critiques": list(frozen_critiques),
        "selector_decision": decision_record,
        "host_issued_result": issued,
        "audit": {
            "partition_manifest": partition_audit,
            "candidate_set_fingerprint": frozen_set_fp,
            "critique_set_fingerprint": critique_set_fp,
            "partitions_validated_before_generation": True,
            "candidates_frozen_before_any_review": True,
            "rivals_hidden_until_all_candidates_frozen": True,
            "adversaries_saw_one_sanitized_candidate_each": True,
            "selector_visible_input_types": [
                "constitution",
                "sanitized_frozen_candidates",
                "sanitized_blinded_critiques",
            ],
            "selector_mutation_authority": False,
            "selector_called": selector_called,
            "host_issuance_authority": True,
        },
    }
    return freeze(result)


__all__ = [
    "BLINDED_ADVERSARY_ROLE",
    "COGNITION_VERSION",
    "CROSS_DOMAIN_ARCHITECTURE_ANALOGIST",
    "FAILURE_EXPERIENCED_OPERATOR",
    "FrozenDict",
    "INVENTOR_ROLES",
    "PRODUCT_OPPORTUNITY_INVENTOR",
    "SELECTOR_MODES",
    "SELECTOR_ROLE",
    "fingerprint",
    "freeze",
    "partition_cognition_evidence_bundle",
    "run_partitioned_product_cognition",
    "thaw",
]
