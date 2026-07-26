# Multi-agent team integration

Palamedes can cooperate with a Paperclip-style agent team without becoming the
team's scheduler or manager. The host still owns wakes, budgets, permissions,
queues, and process lifecycle. Palamedes owns a shared epistemic layer:

```text
specialist observations
  -> provenance and observation-surface ledger
  -> competing falsifiable hypotheses
  -> one-owner mission claims
  -> planner and implementation agents
  -> outcomes with explicit contribution attribution
  -> revised shared world state
```

The reference implementation is
`scaffolds/palamedes_agents/src/palamedes_agents/team_cognition.py`. It ships
with the main `palamedes` package and is also available from the standalone
agent scaffold.

## Why this is separate from the plan

The current plan is an authoritative commitment. Team cognition is deliberately
plural:

- two agents may preserve incompatible hypotheses;
- observations keep the agent, role, source, time, commit, confidence, observed
  population, missing perspectives, and selection bias;
- a world version prevents stale writes;
- a mission has one active owner so two workers do not silently duplicate it;
- an outcome separates mission selection, planning, implementation,
  environment, and measurement contributions instead of crediting Palamedes
  merely because it participated.

This avoids both failure modes: Palamedes does not command every worker, and
workers do not create private, mutually inconsistent copies of the world.

## Independent exploration

Role labels alone do not create cognitive diversity. When several agents should
originate opportunities, use a commit–reveal round:

1. `palamedes team round-begin` freezes the question, participants, and evidence
   boundary.
2. Each agent creates a private candidate and nonce, then obtains its digest
   with `palamedes team candidate-hash`.
3. Each submits only the digest through `candidate-commit`. No candidate prose
   is present in shared state during this phase.
4. After every participant commits, each submits the candidate and nonce through
   `candidate-reveal`.
5. A mismatched reveal is rejected. Only after all valid reveals does the round
   become `ready` for Palamedes comparison.

This does not guarantee originality, but it prevents the first visible proposal
from silently anchoring every later agent.

## Host integration

Each host agent should use a stable `agent_id`. Before proposing a mission it
records observations and hypotheses; before implementation it claims the
mission. The host passes the same state path to every local worker:

```bash
palamedes team observe \
  --state .palamedes/team-cognition.json \
  --payload-json '{
    "observation_id":"obs-hot-seat-flow",
    "agent_id":"ux-agent",
    "agent_role":"researcher",
    "kind":"fact",
    "content":"The current game passes one phone between players.",
    "source":"repository:mobile/lib/screens/games/yut_game_screen.dart",
    "observation_surface":"implemented local game flow",
    "confidence":85,
    "coverage":{
      "observed_population":"implemented flow",
      "missing_perspectives":["real family play"],
      "selection_bias":"code proves capability, not user behavior"
    }
  }'
```

Use `--expected-world-version` when an agent's decision depends on an exact
snapshot. A stale writer fails and must reread rather than overwrite another
agent's observation.

Record a competing hypothesis without resolving it by authority:

```bash
palamedes team hypothesis \
  --payload-json '{
    "hypothesis_id":"hyp-handoff-ritual",
    "agent_id":"ux-agent",
    "statement":"Phone hand-off can become a turn ritual.",
    "mechanism":"A private transition can clarify ownership.",
    "prediction":"Wrong-player actions decline.",
    "falsifier":"The transition slows play without reducing errors.",
    "evidence_ids":["obs-hot-seat-flow"]
  }'
```

After work, the owning host must use `team-release --status completed` or
`team-release --status released`; ownership is never silently transferred.
New evidence changes a hypothesis through `team-hypothesis-update`, preserving
the prior statement and a revision record instead of rewriting history.

The programmatic cycle accepts an optional `TeamCognitionStore`. A team-enabled
cycle requires `context.agent_id`, can record `context.observation`, can claim
`context.mission_id`, and injects the current `team_cognition` snapshot into
the strategist payload. Existing single-agent cycles remain unchanged when no
team store is supplied.

The normal Palamedes terminal can consume the same state:

```bash
palamedes chat \
  --provider codex \
  --workspace /path/to/project \
  --team-state /path/to/project/.palamedes/team-cognition.json \
  --agent-id palamedes-main \
  --agent-role strategist
```

The shared snapshot is supplied to ordinary chat reasoning and every `/cycle`
role. It is evidence context, not permission to execute or a scalar team vote.
The durable ledger retains full history, while reasoning receives a bounded
context containing counts, recent observations and outcomes, open hypotheses,
active missions, and only exploration rounds whose candidates are fully
revealed. Unrevealed candidates never enter another agent's prompt.

## Boundaries

- This JSON implementation is a local-host vertical slice, not a distributed
  database.
- `flock` and atomic replacement prevent lost local concurrent writes.
- Cross-machine teams should place the same contract behind transactional
  storage and compare `world_version`.
- Team size does not prove viewpoint diversity. Agents need different evidence
  surfaces and failure concerns, not merely different role names.
- Structural correctness does not prove that Palamedes improves product
  outcomes. Compare solo Codex, Codex plus Palamedes, and team plus Palamedes
  with frozen information and downstream outcome evidence.
