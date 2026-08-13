# Integrations

<p align="center">
  <strong>English</strong> · <a href="integrations.ko.md">한국어</a>
</p>

Palamedes is designed to sit upstream of execution agents. The host retains
process lifecycle, credentials, side effects, approval, and delivery authority.

## Integration surfaces

| Surface | Use |
| --- | --- |
| CLI | Local human and agent workflows |
| HTTP API | Language-neutral plan-state access |
| Python client | Typed convenience methods and retry behavior |
| Agent wrapper | Bounded mission drafting and handoff |
| Reference adapters | Experimental host patterns |

## HTTP server

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

Read endpoints include `/plan`, `/qa`, `/health`, `/cycle`, `/history`,
`/validate`, and `/tools`. Writes include `/plan`, `/evidence`, `/replan`,
restore operations, and generic tool execution. Safe writes use the current
plan fingerprint to reject stale state.

## Python client

```python
from palamedes_sdk import PalamedesClient

client = PalamedesClient("http://127.0.0.1:8787")
cycle = client.get_cycle(history_limit=5)
updated = client.update_plan({"goal": "Ship a validated agent layer"})
```

The client supports stale-write handling, refresh-and-retry policy, post-write
cycle snapshots, restore flows, idempotency keys, and optional health-gated
writes.

## Host responsibilities

A host should:

1. Supply bounded, provenance-aware context.
2. Keep planning and execution identities separate.
3. Require explicit approval before delivery work.
4. Return observable outcomes without declaring attribution prematurely.
5. Respect fingerprint conflicts and restore lineage.

## Custom cognition providers

Provider selection is registry-based. A host can add a provider without
changing the cognition cycle by registering a `ProviderRegistration` before
constructing the CLI parser or calling `provider_from_config`.

```python
from palamedes_chat import (
    ProviderCapability,
    ProviderRegistration,
    register_chat_provider,
)

register_chat_provider(
    ProviderRegistration(
        capability=ProviderCapability(
            name="company-llm",
            transport="internal-gateway",
            default_model="reasoner-v1",
            supports_streaming=True,
            supports_usage=True,
            structured_json_mode="prompt_validated",
            credential_kind="workload_identity",
        ),
        factory=lambda config: CompanyProvider(config),
        health=lambda config: {
            "provider": "company-llm",
            "status": "ok",
            "credential_hint": "workload identity",
        },
    )
)
```

The provider object implements `stream(messages)` and exposes stable
`provider_name`, `model`, and optional `last_usage`. Capability metadata is
discoverable through `provider_capabilities()`. Registration does not grant
tool, delivery, or decision authority; providers only supply bounded cognition
outputs to the existing validators.

## Detailed guides

- [AgentScope integration](integration-agentscope.md)
- [Agent team integration](integration-agent-teams.md)
- [Agents bootstrap](palamedes-agents-bootstrap.md)
- [Agent skills](palamedes-agents-skills.md)
- [Pre-planner contract](palamedes-pre-planner-contract.md)
- [Reference agent patterns](reference-agent-patterns.md)
- [Python SDK](../palamedes_sdk/client.py)
- [TypeScript consumer](../palamedes_reference_consumer.ts)
- [Kernel adapter example](../examples/palamedes_kernel_adapter.py)
- [Planner host example](../examples/palamedes_planner_host.py)

Reference surfaces are experimental unless [STABILITY.md](../STABILITY.md)
states otherwise.
