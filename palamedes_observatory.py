#!/usr/bin/env python3
"""Read-only projection of Palamedes planning history and live decision state."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


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
    }


def render_cli(snapshot: Dict[str, Any]) -> str:
    summary = snapshot["summary"]
    lines = [
        "Palamedes Observatory (read-only)",
        "  " + "  ".join(f"{key}={value}" for key, value in summary.items()),
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
.card,.event{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}.card b{display:block;font-size:24px;color:var(--accent)}
#filters{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}button{background:#202a45;color:#dce6ff;border:1px solid #34415f;border-radius:20px;padding:7px 12px;cursor:pointer}button.on{border-color:var(--accent);color:var(--accent)}
.event{display:grid;grid-template-columns:160px 90px 140px 1fr;gap:12px;margin:8px 0}.kind{text-transform:uppercase;color:var(--accent);font-weight:700}.title{font-weight:700}.id,.summary{color:var(--muted);font-size:12px;word-break:break-all}details{margin-top:8px}pre{white-space:pre-wrap;max-height:360px;overflow:auto;background:#0d1427;padding:10px;border-radius:8px}
@media(max-width:720px){.event{grid-template-columns:1fr}.event>*{margin:0}}
</style></head><body><main><header><div><h1>Palamedes Observatory</h1><div class="muted">관측 → 기획 → 선택 → 미션 → 결과의 read-only 이력</div></div><div id="updated" class="muted"></div></header><section id="cards"></section><nav id="filters"></nav><section id="events"></section></main>
<script>
let data={events:[],summary:{}}, active='all', signature='';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function draw(){cards.innerHTML=Object.entries(data.summary).map(([k,v])=>`<div class=card><span class=muted>${esc(k)}</span><b>${v}</b></div>`).join('');
const kinds=['all',...new Set(data.events.map(e=>e.kind))];filters.innerHTML=kinds.map(k=>`<button class="${k===active?'on':''}" data-k="${k}">${k}</button>`).join('');
filters.querySelectorAll('button').forEach(b=>b.onclick=()=>{active=b.dataset.k;draw()});
events.innerHTML=data.events.filter(e=>active==='all'||e.kind===active).map(e=>`<article class=event><time>${esc(e.ts||'-')}</time><div class=kind>${esc(e.kind)}</div><div>${esc(e.status)}</div><div><div class=title>${esc(e.title)}</div><div class=id>${esc(e.id)}</div><div class=summary>${esc(e.summary)}</div><details><summary>기획 내용 펼치기</summary><pre>${esc(JSON.stringify(e.details,null,2))}</pre></details></div></article>`).join('')||'<p class=muted>기록이 없습니다.</p>';updated.textContent='updated '+new Date().toLocaleTimeString();}
async function load(){const r=await fetch('/observatory?limit=300',{cache:'no-store'}), next=await r.json(), nextSignature=JSON.stringify(next);if(nextSignature===signature)return;signature=nextSignature;data=next;draw()}load();setInterval(load,5000);
</script></body></html>"""
