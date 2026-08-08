#!/usr/bin/env python3
"""Read-only projection of Palamedes planning history and live decision state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from palamedes_lifecycle import reconcile_lifecycle
from palamedes_product_alignment import ProductAlignmentStore
from palamedes_satisfaction import SatisfactionStore, assessment_is_current
from palamedes_storage import inventory_storage


def _json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _first(row: Dict[str, Any], fields: Iterable[str]) -> str:
    for field in fields:
        value = str(row.get(field, "")).strip()
        if value:
            return value
    return ""


def _event(
    row: Dict[str, Any], *, kind: str, identifier: str, title: str,
    summary: str = "", details: Any = None,
) -> Dict[str, Any]:
    return {
        "ts": _first(
            row,
            (
                "completed_at", "recorded_at", "approved_at", "rejected_at",
                "failed_at", "created_at", "opened_at", "updated_at", "started_at", "ts",
            ),
        ),
        "kind": kind,
        "id": identifier,
        "status": _first(row, ("status", "decision", "mission_disposition")) or "recorded",
        "title": title or identifier,
        "summary": summary,
        "details": details if details is not None else {},
        "lineage": {
            key: row[key]
            for key in (
                "vision_genesis_id", "vision_scout_id", "cognition_cycle_id",
                "mission_contract_id", "outcome_id", "selected_candidate_id",
            )
            if row.get(key)
        },
    }


def _tree_size(root: Path) -> int:
    total = 0
    if not root.is_dir():
        return 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
        except OSError:
            continue
    return total


def build_operations_board(state_dir: Path) -> Dict[str, Any]:
    mission_root = state_dir / "missions"
    lifecycle = reconcile_lifecycle(mission_root)
    alignment = ProductAlignmentStore(state_dir / "product-alignment").active_context()
    satisfaction = SatisfactionStore(state_dir / "satisfaction").latest()
    missions = [_json(path) for path in sorted(mission_root.glob("mission-*.json"))]
    cycles = [_json(path) for path in sorted((mission_root / "cognition").glob("cycle-*.json"))]
    latest_cycle = max(
        cycles,
        key=lambda row: _first(row, ("completed_at", "updated_at", "failed_at", "started_at", "created_at")),
        default={},
    )
    latest_usage = latest_cycle.get("provider_usage", {})
    totals = latest_usage.get("totals", {}) if isinstance(latest_usage, dict) else {}
    state_counts: Dict[str, int] = {}
    for item in lifecycle["items"]:
        state = str(item.get("projected_state", "unknown"))
        state_counts[state] = state_counts.get(state, 0) + 1
    mission_status_counts: Dict[str, int] = {}
    for mission in missions:
        status = str(mission.get("status", "unknown"))
        mission_status_counts[status] = mission_status_counts.get(status, 0) + 1
    workspace_root = state_dir.parent
    stale_assessments = [
        row
        for row in satisfaction
        if row.get("evidence_state") == "verified_stale"
        or not assessment_is_current(workspace_root, row)
    ]
    misaligned_assessments = [
        row for row in satisfaction
        if row.get("evidence_state") == "misaligned_implementation"
    ]
    next_decisions = []
    for gate in lifecycle["items"]:
        if gate.get("projected_state") == "follow_up_required":
            next_decisions.append({
                "kind": "follow_up_required",
                "id": gate.get("handoff_id"),
                "summary": "Resolve or explicitly carry the open successor obligation.",
            })
        elif gate.get("projected_state") in {
            "handed_off", "acknowledged_by_implementer", "executing", "evidence_submitted"
        }:
            next_decisions.append({
                "kind": "active_mission",
                "id": gate.get("mission_contract_id"),
                "summary": "Execute the active mission, submit evidence, or record an honest blocked outcome.",
            })
    for conflict in lifecycle["conflicts"]:
        next_decisions.append({
            "kind": "lifecycle_conflict",
            "id": conflict.get("handoff_id"),
            "summary": ", ".join(conflict.get("reasons", [])),
        })
    for assessment in stale_assessments:
        next_decisions.append({
            "kind": "refresh_evidence",
            "id": assessment.get("requirement_id"),
            "summary": "Refresh evidence against the current workspace snapshot.",
        })
    for assessment in misaligned_assessments:
        next_decisions.append({
            "kind": "misaligned_implementation",
            "id": assessment.get("requirement_id"),
            "summary": "Stop implementation expansion and resolve product-purpose conflict.",
        })
    for gap in alignment.get("integration_gaps", []):
        next_decisions.append({
            "kind": "integration_gap",
            "id": gap.get("gap_id"),
            "summary": str(gap.get("observed_path", "")),
        })
    active_mission_ids = {
        str(item.get("mission_contract_id", ""))
        for item in lifecycle["items"]
        if item.get("projected_state") in {
            "handed_off", "acknowledged_by_implementer", "executing", "evidence_submitted"
        }
    }
    active_missions = [mission for mission in missions if mission.get("mission_id") in active_mission_ids]
    storage = inventory_storage(state_dir)
    gate_resolutions = _jsonl(mission_root / "gate-resolution-events.jsonl")
    return {
        "operations_board_version": "palamedes-operations-board/1",
        "read_only": True,
        "product": {
            "surface_count": len(alignment.get("surfaces", {})),
            "surfaces": alignment.get("surfaces", {}),
            "global_purpose_count": len([
                row for row in alignment.get("purposes", []) if not row.get("surface_key")
            ]),
            "open_integration_gaps": len(alignment.get("integration_gaps", [])),
        },
        "missions": {
            "total": len(missions),
            "status_counts": dict(sorted(mission_status_counts.items())),
            "draft_candidates": sum(1 for row in missions if row.get("status") == "draft"),
            "active": [
                {
                    "mission_id": row.get("mission_id"),
                    "mission": row.get("mission"),
                    "surface_key": row.get("surface_key"),
                    "status": row.get("status"),
                }
                for row in active_missions[-10:]
            ],
        },
        "lifecycle": {
            "state_counts": dict(sorted(state_counts.items())),
            "conflicts": lifecycle["summary"]["conflicts"],
            "orphans": lifecycle["summary"]["orphan_outcomes"],
            "pending_reconcile_proposals": lifecycle["summary"]["proposals"],
            "proposal_fingerprint": lifecycle["proposal_fingerprint"],
        },
        "evidence": {
            "assessment_count": len(satisfaction),
            "already_satisfied": len([
                row for row in satisfaction
                if row.get("disposition") == "already_satisfied"
                and assessment_is_current(workspace_root, row)
            ]),
            "stale": len(stale_assessments),
            "misaligned": len(misaligned_assessments),
            "gate_resolutions": len(gate_resolutions),
            "latest_gate_resolution": (
                gate_resolutions[-1].get("resolution_id") if gate_resolutions else ""
            ),
        },
        "latest_cycle": {
            "cycle_id": latest_cycle.get("cognition_cycle_id", ""),
            "mode": latest_cycle.get("cycle_mode", "legacy-or-component"),
            "status": latest_cycle.get("status", ""),
            "provider_calls": latest_usage.get("attempted_calls", 0) if isinstance(latest_usage, dict) else 0,
            "tokens": totals.get("total_tokens", 0) if isinstance(totals, dict) else 0,
        },
        "storage": {
            "state_bytes": _tree_size(state_dir),
            "mission_bytes": _tree_size(mission_root),
            **storage["summary"],
            "classification_counts": storage["classification_counts"],
            "inventory_fingerprint": storage["inventory_fingerprint"],
            "read_only": True,
        },
        "next_decisions": next_decisions[:20],
    }


def build_observatory(state_dir: Path, *, limit: int = 200) -> Dict[str, Any]:
    if limit < 0:
        raise ValueError("limit must be non-negative")
    events: List[Dict[str, Any]] = []

    visions = [_json(path) for path in sorted((state_dir / "visions" / "records").glob("*.json"))]
    scouts = [_json(path) for path in sorted((state_dir / "vision-scouts").glob("vision-scout-*.json"))]
    inventions = [_json(path) for path in sorted((state_dir / "inventions" / "records").glob("invention-*.json"))]
    pursuits = [_json(path) for path in sorted((state_dir / "pursuits" / "records").glob("pursuit-*.json"))]
    cycles = [_json(path) for path in sorted((state_dir / "missions" / "cognition").glob("cycle-*.json"))]
    missions = [_json(path) for path in sorted((state_dir / "missions").glob("mission-*.json"))]
    outcomes = _jsonl(state_dir / "missions" / "outcomes.jsonl")
    gates = _jsonl(state_dir / "missions" / "outcome-gates.jsonl")
    revisions = _jsonl(state_dir / "revisions.jsonl")

    for row in visions:
        judgment = row.get("judgment", {}) if isinstance(row.get("judgment"), dict) else {}
        events.append(_event(
            row,
            kind="vision",
            identifier=str(row.get("vision_genesis_id", "vision")),
            title=str(judgment.get("vision_brief", ""))[:140] or "Vision Genesis",
            summary=f"decision={judgment.get('decision', row.get('status', ''))}",
            details={
                "judgment": judgment,
                "product_worlds": row.get("product_worlds", {}),
                "requirement_gate": row.get("requirement_gate", {}),
            },
        ))
    for row in scouts:
        events.append(_event(
            row,
            kind="scout",
            identifier=str(row.get("vision_scout_id", "scout")),
            title=str(row.get("selected_founder_prompt", ""))[:140] or "Vision Scout",
            summary=f"decision={row.get('governor', {}).get('decision', row.get('status', ''))}",
            details={
                "selected_founder_prompt": row.get("selected_founder_prompt", ""),
                "originator": row.get("originator", {}),
                "critic": row.get("critic", {}),
                "governor": row.get("governor", {}),
            },
        ))
    for row in inventions:
        provenance = row.get("provenance", {}) if isinstance(row.get("provenance"), dict) else {}
        events.append(_event(
            row,
            kind="invention",
            identifier=str(row.get("product_invention_id", "invention")),
            title=f"Product invention · {row.get('selected_candidate_id') or row.get('status', '')}",
            summary=f"candidates={len(row.get('candidates', []))} origin={provenance.get('origin', '')}",
            details={
                "affect_dependency_map": row.get("affect_dependency_map", {}),
                "candidates": row.get("candidates", []),
                "playable_contracts": row.get("playable_contracts", []),
                "adversary": row.get("adversary", {}),
                "selector": row.get("selector", {}),
                "provenance": provenance,
                "delivery_authority_granted": row.get("delivery_authority_granted", False),
            },
        ))
    for row in pursuits:
        routing = row.get("epistemic_routing", {}) if isinstance(row.get("epistemic_routing"), dict) else {}
        events.append(_event(
            row,
            kind="pursuit",
            identifier=str(row.get("pursuit_id", "pursuit")),
            title=str(row.get("objective", ""))[:140] or "Domain-general pursuit",
            summary=f"types={','.join(routing.get('task_types', []))} execution_started={row.get('execution_started', False)}",
            details={
                "intent": row.get("intent", {}),
                "epistemic_routing": routing,
                "unknown_map": row.get("unknown_map", {}),
                "capability_composition": row.get("capability_composition", {}),
                "adversary": row.get("adversary", {}),
                "governor": row.get("governor", {}),
                "authority": {
                    "external": row.get("external_action_authority_granted", False),
                    "publication": row.get("publication_authority_granted", False),
                    "financial": row.get("financial_action_authority_granted", False),
                },
            },
        ))
    for row in cycles:
        events.append(_event(
            row,
            kind="cycle",
            identifier=str(row.get("cognition_cycle_id", "cycle")),
            title=f"Cognition cycle · {row.get('decision', row.get('status', ''))}",
            summary=f"roles={len(row.get('artifacts', []))} selected={row.get('selected_candidate_id', '')}",
            details={
                "decision": row.get("decision", ""),
                "selected_candidate_id": row.get("selected_candidate_id", ""),
                "candidate_fates": row.get("candidate_fates", []),
                "failure": row.get("failure", ""),
            },
        ))
    for row in missions:
        events.append(_event(
            row,
            kind="mission",
            identifier=str(row.get("mission_id", "mission")),
            title=str(row.get("mission", ""))[:140] or "Mission",
            summary=str(row.get("success_metric", ""))[:180],
            details={
                "success_metric": row.get("success_metric", ""),
                "constraints": row.get("constraints", []),
                "non_goals": row.get("non_goals", []),
                "falsifiers": row.get("falsifiers", []),
                "candidate_fates": row.get("candidate_fates", []),
            },
        ))
    for row in outcomes:
        events.append(_event(
            row,
            kind="outcome",
            identifier=str(row.get("outcome_id", "outcome")),
            title=str(row.get("observation", ""))[:140] or "Outcome",
            summary=f"mission={row.get('mission_contract_id', '')}",
            details=row,
        ))

    latest_gates: Dict[str, Dict[str, Any]] = {}
    for row in gates:
        gate_id = str(row.get("gate_id", ""))
        if gate_id:
            latest_gates[gate_id] = row
    for row in latest_gates.values():
        events.append(_event(
            row,
            kind="gate",
            identifier=str(row.get("gate_id", "gate")),
            title=str(row.get("required_response", ""))[:140] or "Evidence gate",
            summary=f"mission={row.get('mission_contract_id', '')}",
            details=row,
        ))
    for row in revisions:
        events.append(_event(
            row,
            kind="revision",
            identifier=str(row.get("revision_id", "revision")),
            title=str(row.get("reason", ""))[:140] or str(row.get("source", "Plan revision")),
            summary=f"source={row.get('source', '')}",
            details={"reason": row.get("reason", ""), "metadata": row.get("metadata", {})},
        ))

    events.sort(key=lambda row: (row["ts"], row["kind"], row["id"]), reverse=True)
    if limit:
        events = events[:limit]
    elif limit == 0:
        events = []
    open_gates = [row for row in latest_gates.values() if row.get("status") == "open"]
    return {
        "observatory_version": "palamedes-observatory/1",
        "read_only": True,
        "summary": {
            "visions": len(visions),
            "scouts": len(scouts),
            "inventions": len(inventions),
            "pursuits": len(pursuits),
            "cycles": len(cycles),
            "missions": len(missions),
            "outcomes": len(outcomes),
            "open_gates": len(open_gates),
            "revisions": len(revisions),
        },
        "current": {
            "latest_vision_id": visions[-1].get("vision_genesis_id", "") if visions else "",
            "latest_invention_id": inventions[-1].get("product_invention_id", "") if inventions else "",
            "latest_pursuit_id": pursuits[-1].get("pursuit_id", "") if pursuits else "",
            "latest_cycle_id": cycles[-1].get("cognition_cycle_id", "") if cycles else "",
            "open_gates": open_gates,
        },
        "events": events,
        "event_limit": limit,
        "operations_board": build_operations_board(state_dir),
    }


def render_cli(snapshot: Dict[str, Any]) -> str:
    summary = snapshot["summary"]
    board = snapshot.get("operations_board", {})
    lifecycle = board.get("lifecycle", {})
    evidence = board.get("evidence", {})
    latest_cycle = board.get("latest_cycle", {})
    storage = board.get("storage", {})
    lines = [
        "Palamedes Observatory (read-only)",
        "  " + "  ".join(f"{key}={value}" for key, value in summary.items()),
        "  lifecycle=" + json.dumps(lifecycle.get("state_counts", {}), sort_keys=True)
        + f" conflicts={lifecycle.get('conflicts', 0)} orphans={lifecycle.get('orphans', 0)}",
        f"  evidence=current:{evidence.get('already_satisfied', 0)} "
        f"stale:{evidence.get('stale', 0)} misaligned:{evidence.get('misaligned', 0)}",
        f"  latest_cycle={latest_cycle.get('cycle_id') or '-'} "
        f"mode={latest_cycle.get('mode') or '-'} calls={latest_cycle.get('provider_calls', 0)} "
        f"tokens={latest_cycle.get('tokens', 0)}",
        f"  next_decisions={len(board.get('next_decisions', []))}",
        f"  storage=logical:{storage.get('logical_bytes', 0)} "
        f"unique:{storage.get('unique_content_bytes', 0)} "
        f"reclaimable:{storage.get('duplicate_reclaimable_bytes', 0)} "
        f"duplicates:{storage.get('duplicate_groups', 0)} (read-only)",
    ]
    for event in snapshot["events"]:
        lines.append(
            f"{event['ts'] or '-'} | {event['kind']:<8} | {event['status']:<16} | "
            f"{event['id']} | {event['title']}"
        )
    return "\n".join(lines)


def render_web_shell() -> str:
    """Return a dependency-free read-only UI; data remains sourced from JSON API."""
    return """<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="icon" href="data:,">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Palamedes Observatory</title><style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#151c31;--muted:#91a0bd;--line:#29334d;--accent:#75e6c4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#edf2ff;font:14px/1.5 system-ui,sans-serif}
main{max-width:1180px;margin:auto;padding:32px 20px}header{display:flex;justify-content:space-between;gap:20px;align-items:end}
h1{margin:0;font-size:30px}.muted{color:var(--muted)}#cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;margin:24px 0}
.card,.event,.decision{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}.card b{display:block;font-size:24px;color:var(--accent)}
#board{margin:20px 0}.board-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}.decision{margin:8px 0}.decision b{color:#ffd37a}.section-title{margin:22px 0 8px}
#filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}button{background:#202a45;color:#dce6ff;border:1px solid #34415f;border-radius:20px;padding:7px 12px;cursor:pointer}button.on{border-color:var(--accent);color:var(--accent)}
.event{display:grid;grid-template-columns:160px 90px 140px 1fr;gap:12px;margin:8px 0}.kind{text-transform:uppercase;color:var(--accent);font-weight:700}.title{font-weight:700}.id,.summary{color:var(--muted);font-size:12px;word-break:break-all}details{margin-top:8px}pre{white-space:pre-wrap;max-height:360px;overflow:auto;background:#0d1427;padding:10px;border-radius:8px}
@media(max-width:720px){.event{grid-template-columns:1fr}.event>*{margin:0}}
</style></head><body><main><header><div><h1>Palamedes Observatory</h1><div class="muted">Current purpose, active work, evidence, and next decisions</div></div><div id="updated" class="muted"></div></header><section id="board"></section><h2 class="section-title">History</h2><section id="cards"></section><nav id="filters"></nav><section id="events"></section></main>
<script>
let data={events:[],summary:{}}, active='all', signature='';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function draw(){const b=data.operations_board||{}, lifecycle=b.lifecycle||{}, evidence=b.evidence||{}, cycle=b.latest_cycle||{}, storage=b.storage||{}, decisions=b.next_decisions||[];
board.innerHTML=`<div class=board-grid><div class=card><span class=muted>Active missions</span><b>${(b.missions?.active||[]).length}</b></div><div class=card><span class=muted>Lifecycle conflicts</span><b>${lifecycle.conflicts||0}</b></div><div class=card><span class=muted>Evidence stale / misaligned</span><b>${evidence.stale||0} / ${evidence.misaligned||0}</b></div><div class=card><span class=muted>Latest cycle calls / tokens</span><b>${cycle.provider_calls||0} / ${cycle.tokens||0}</b></div><div class=card><span class=muted>Duplicate reclaimable bytes</span><b>${storage.duplicate_reclaimable_bytes||0}</b></div></div><h2 class=section-title>Next decisions</h2>${decisions.map(d=>`<div class=decision><b>${esc(d.kind)}</b> · ${esc(d.id||'-')}<div class=muted>${esc(d.summary)}</div></div>`).join('')||'<p class=muted>No pending decisions.</p>'}`;
cards.innerHTML=Object.entries(data.summary).map(([k,v])=>`<div class=card><span class=muted>${esc(k)}</span><b>${v}</b></div>`).join('');
const kinds=['all',...new Set(data.events.map(e=>e.kind))];filters.innerHTML=kinds.map(k=>`<button class="${k===active?'on':''}" data-k="${k}">${k}</button>`).join('');
filters.querySelectorAll('button').forEach(b=>b.onclick=()=>{active=b.dataset.k;draw()});
events.innerHTML=data.events.filter(e=>active==='all'||e.kind===active).map(e=>`<article class=event><time>${esc(e.ts||'-')}</time><div class=kind>${esc(e.kind)}</div><div>${esc(e.status)}</div><div><div class=title>${esc(e.title)}</div><div class=id>${esc(e.id)}</div><div class=summary>${esc(e.summary)}</div><details><summary>기획 내용 펼치기</summary><pre>${esc(JSON.stringify(e.details,null,2))}</pre></details></div></article>`).join('')||'<p class=muted>기록이 없습니다.</p>';updated.textContent='updated '+new Date().toLocaleTimeString();}
async function load(){const r=await fetch('/observatory?limit=300',{cache:'no-store'}), next=await r.json(), nextSignature=JSON.stringify(next);if(nextSignature===signature)return;signature=nextSignature;data=next;draw()}load();setInterval(load,5000);
</script></body></html>"""
