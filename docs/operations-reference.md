# Operations Reference

<p align="center">
  <strong>English</strong> · <a href="operations-reference.ko.md">한국어</a>
</p>

## Command groups

```text
plan, replan                 create or revise direction
evidence, hypothesis         record claims and uncertainty
view, inquiry, encounter     preserve changes of perspective
probe                        register a learning-producing development step
observe, watch               collect bounded workspace signals
qa, validate, health         inspect state and contract quality
history, restore             inspect and recover revisions
chat                         run provider-backed cognition workflows
workspace                    register and select repositories
```

Run `palamedes --help` or `palamedes <command> --help` for complete flags.

## Fingerprints and concurrency

Every writable plan has a fingerprint. Clients should supply the expected
fingerprint when mutating state. A mismatch is a conflict, not permission to
overwrite. Refresh the plan, reconsider the mutation, and retry only when the
new state still supports it.

## Restore

Restore creates a new revision from a recoverable historical state; it does not
delete intervening history. Preview the target before restoring and retain the
new fingerprint returned by the operation.

## Storage

The default state root is `.palamedes/` inside the selected workspace. State is
local-first and includes revisions, events, mission records, observations, and
workflow-specific stores. Use `palamedes health` and `palamedes storage` to
inspect consistency.

## HTTP API

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

Common endpoints:

```text
GET  /plan /qa /health /cycle /history /validate /tools
POST /plan /evidence /replan /restore/preview /restore
POST /tools/<tool_name>
POST /tools/execute
POST /agent/act
```

See the server's `/tools` response for the current executable surface.

## Development verification

```bash
make compile
make test
make scaffold-test
make schema-check
make package-check
make check
```

## Contract references

- [Stability levels](../STABILITY.md)
- [Contract versioning](../CONTRACT_VERSIONING.md)
- [Contributing](../CONTRIBUTING.md)
- [Plan schema](../schemas/plan.schema.json)
- [SDK client](../palamedes_sdk/client.py)

Operational commands can mutate local Palamedes state. Execution agents and
external systems remain outside Palamedes authority unless the host explicitly
invokes them.
