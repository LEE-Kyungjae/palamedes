#!/usr/bin/env python3
from typing import Any, Dict, List

from palamedes_agents.runtime.host_step import role_has_action_capabilities
from palamedes_agents.workflows.strategy_loop import validate_strategy_report_shape


def route_strategy_next_actions(report: Dict[str, Any]) -> Dict[str, Any]:
    errors = validate_strategy_report_shape(report)
    if errors:
        raise ValueError("invalid strategy report: " + "; ".join(errors))

    routes: List[Dict[str, Any]] = []
    for index, item in enumerate(report.get("next_actions", [])):
        target_role = str(item.get("target_role", "")).strip()
        action = str(item.get("action", "")).strip()
        executable = role_has_action_capabilities(target_role, action)
        routes.append(
            {
                "index": index,
                "target_role": target_role,
                "action": action,
                "priority": str(item.get("priority", "")).strip(),
                "executable": executable,
                "reason": str(item.get("reason", "")).strip(),
                "payload": item.get("payload", {}),
                "blocker": "" if executable else "target_role_lacks_action_capability",
            }
        )

    return {
        "ok": all(route["executable"] for route in routes),
        "type": "strategy_action_routes",
        "decision": str(report.get("decision", "")).strip(),
        "routes": routes,
    }
