# Palamedes Agents Skill Model

This document proposes a skill model for the separate `palamedes-agents` repo.

It does not change the Palamedes kernel boundary.
Palamedes remains `plan-only`.
Skills belong to the orchestration/runtime layer around Palamedes, not to the kernel itself.

## Thesis

`palamedes-agents` should be:

- capability-gated
- role-oriented
- skill-configured
- runtime-injected

That means:

- Palamedes owns plan state and mutation contracts
- the host action contract owns what actions are allowed
- skills shape how an agent reasons and operates within those allowed actions
- runtime decides which skills are actually injected for one session

The important separation is:

- capability answers "may this agent do this?"
- skill answers "how should this agent do it well?"

## Why Not Put Skills In Palamedes

Palamedes should not own:

- skill registry
- prompt pack lifecycle
- provider-specific tool injection
- runtime memory packaging
- session-specific agent composition

Those concerns are unstable and host-specific.
They belong in `palamedes-agents`.

Palamedes should only expose the stable planning surfaces that skills consume:

- `get_cycle`
- `update_plan`
- `capture_evidence_cycle`
- `request_review`
- `resolve_review`
- `preview_restore_previous`
- `restore_previous`

## Core Model

The recommended model has five layers.

### 1. Role

A role is the stable job identity.

Initial roles:

- `planner`
- `strategist`
- `researcher`
- `reviewer`

Role answers:

- what job the agent is trying to perform
- what default operating posture it should have
- which profile in the host action contract it should map to

### 2. Capability

A capability is the hard permission boundary.

Capabilities should come from the existing host action contract, for example:

- `plan.read`
- `plan.write`
- `evidence.append_and_replan`
- `review.request`
- `review.resolve`
- `plan.restore`

Capabilities should stay authoritative in Palamedes-facing contracts.
Skills must never bypass them.

### 3. Skill

A skill is a versioned behavior bundle for a role.

A skill should contain:

- system guidance
- operating heuristics
- allowed tool preferences
- output format expectations
- stop/escalation rules
- optional reusable prompt fragments

A skill should not contain:

- raw permission grants
- direct plan-state mutation authority
- runtime session state

### 4. Profile

A profile is the binding of:

- one role
- one capability set
- one or more default skills

Profiles should remain small and explicit.

Recommended initial profiles:

- `planner_full`
- `strategist_product`
- `researcher_capture`
- `reviewer_restore`

These should map directly to the current host action contract profiles.

### 5. Runtime Assignment

Runtime assignment is the session-specific composition.

Runtime should decide:

- desired skills
- actually injected skills
- disabled skills
- why a skill was omitted
- provider/runtime-specific rendering details

This is where a `paperclip`-like desired-vs-actual skill model is useful.

## Desired vs Actual Skills

`palamedes-agents` should explicitly track both:

- `desired_skills`
- `actual_skills`

This matters because runtime may fail to inject or may intentionally suppress a skill.

Examples:

- a provider does not support one tool-binding format
- a reviewer session intentionally runs in reduced mode
- a host turns off one experimental skill for a tenant or workspace

Recommended runtime record:

```json
{
  "role": "reviewer",
  "profile": "reviewer_restore",
  "desired_skills": ["review-triage", "restore-safety", "human-handoff"],
  "actual_skills": ["review-triage", "human-handoff"],
  "disabled_skills": [
    {
      "name": "restore-safety",
      "reason": "restore capability disabled by host policy"
    }
  ]
}
```

## Recommended Initial Skill Set

Start with a small set of reusable skills.

### Planner Skills

- `plan-framing`
  Focus on direction clarity, planning horizon, review cadence, and option narrowing.
- `qa-recovery`
  Focus on responding to weak QA results without thrashing the plan.
- `human-handoff`
  Focus on when to stop and request review instead of forcing a conclusion.

### Researcher Skills

- `evidence-capture`
  Focus on claim quality, provenance, and replan-ready evidence packaging.
- `reference-discovery`
  Focus on candidate search, shortlist criteria, and rejection rationale.
- `boundary-awareness`
  Prevent drift into execution orchestration or product sprawl.

### Strategist Skills

- `problem-solution-pressure`
  Validate the narrow user, painful problem, current alternative, and solution fit before expanding scope.
- `desire-emotion-map`
  Identify the positive or negative emotional driver that makes a user pay, return, share, or feel loss.
- `experience-loop-design`
  Convert feature ideas into trigger, emotion, action, reward, monetization, and repeat loops.
- `anti-generic-insight`
  Detect generic LLM-built service patterns such as another AI wrapper, dashboard, todo, CRM, or productivity assistant.
- `reference-to-insight`
  Extract behavior patterns, monetization moments, and transferable creative insights from papers, reviews, failures, and successful services.
- `creative-recombination`
  Generate non-generic product directions by transferring behavior patterns from references across domains.
- `personal-planning-profile`
  Track repeated planning weaknesses, weak axes, and overused solution patterns for the current user.
- `mid-project-intake`
  Let Palamedes enter an already-started project using existing artifacts, constraints, traction, and pivot signals.
- `outcome-learning-loop`
  Convert shipped outcomes, usage signals, revenue signals, retention, feedback, and failed assumptions into plan adjustments.

### Reviewer Skills

- `review-triage`
  Focus on queue ordering, `priority`, `stale_after`, and `sla_bucket` handling.
- `restore-safety`
  Focus on restore previews, rollback caution, and revision interpretation.
- `decision-closure`
  Focus on resolving or dismissing escalations with explicit rationale.

## Capability To Skill Mapping

One capability can support multiple skills.
One skill can depend on multiple capabilities.

Recommended initial mapping:

| Capability | Skills that commonly depend on it |
| --- | --- |
| `plan.read` | `plan-framing`, `qa-recovery`, `review-triage`, `restore-safety` |
| `plan.write` | `plan-framing`, `qa-recovery` |
| `evidence.append_and_replan` | `evidence-capture`, `reference-discovery` |
| `strategy.evaluate` | `problem-solution-pressure`, `desire-emotion-map`, `experience-loop-design`, `anti-generic-insight`, `reference-to-insight`, `personal-planning-profile`, `mid-project-intake` |
| `strategy.generate` | `creative-recombination`, `reference-to-insight` |
| `strategy.learn` | `outcome-learning-loop`, `personal-planning-profile` |
| `review.request` | `human-handoff`, `boundary-awareness`, `decision-closure` |
| `review.resolve` | `decision-closure`, `review-triage` |
| `plan.restore` | `restore-safety` |

Important rule:

- a skill may recommend an action
- only a capability permits the action

## Skill Manifest Shape

Each skill should live as a checked-in manifest plus prompt assets.

Recommended repo shape:

```text
palamedes-agents/
  src/palamedes_agents/
    skills/
      registry.py
      manifests/
        plan-framing.json
        qa-recovery.json
        evidence-capture.json
        review-triage.json
      prompts/
        plan-framing.md
        qa-recovery.md
        evidence-capture.md
        review-triage.md
```

Recommended manifest:

```json
{
  "name": "review-triage",
  "version": "v1",
  "role": "reviewer",
  "summary": "Prioritize and resolve open review work without bypassing Palamedes review semantics.",
  "depends_on_capabilities": ["plan.read", "review.resolve"],
  "preferred_actions": ["resolve_review", "preview_restore_previous"],
  "escalation_actions": ["request_review"],
  "input_signals": ["priority", "stale_after", "sla_bucket", "review_recommendation"],
  "prompt_asset": "prompts/review-triage.md"
}
```

## Profile Manifest Shape

Profiles should be separate from skills.

Recommended manifest:

```json
{
  "name": "reviewer_restore",
  "role": "reviewer",
  "capabilities": ["plan.read", "review.request", "review.resolve", "plan.restore"],
  "default_skills": ["review-triage", "restore-safety", "decision-closure"]
}
```

This keeps three things independently evolvable:

- contract permissions
- skill behavior
- runtime assignment

## Runtime Selection Policy

Runtime should resolve skills in this order:

1. start from role default profile
2. load profile default skills
3. apply host policy additions/removals
4. drop skills whose required capabilities are missing
5. record desired vs actual result

Selection should be deterministic.
The same role and policy input should yield the same skill set.

## Example Session Shapes

### Planner Session

```json
{
  "role": "planner",
  "profile": "planner_full",
  "desired_skills": ["plan-framing", "qa-recovery", "human-handoff"],
  "actual_skills": ["plan-framing", "qa-recovery", "human-handoff"]
}
```

### Research Session

```json
{
  "role": "researcher",
  "profile": "researcher_capture",
  "desired_skills": ["evidence-capture", "reference-discovery", "boundary-awareness"],
  "actual_skills": ["evidence-capture", "reference-discovery", "boundary-awareness"]
}
```

### Reviewer Session

```json
{
  "role": "reviewer",
  "profile": "reviewer_restore",
  "desired_skills": ["review-triage", "restore-safety", "decision-closure"],
  "actual_skills": ["review-triage", "restore-safety", "decision-closure"]
}
```

## Guardrails

The `palamedes-agents` repo should enforce these rules:

- skills cannot grant capabilities
- skills cannot directly redefine Palamedes contracts
- runtime must record omitted skills
- action dispatch must still validate against host action contract
- provider-specific prompt formatting must not leak into the skill semantic model

## First Implementation Plan

The first usable milestone for `palamedes-agents` should be:

1. add profile manifests mirroring `spec/host-action-contract.json`
2. add 6-9 initial skill manifests
3. add a registry that resolves `desired_skills` and `actual_skills`
4. emit runtime session state showing role/profile/skills
5. keep all Palamedes writes routed through one adapter

Do not start by building:

- a marketplace
- dynamic skill downloads
- per-tenant visual skill editors
- arbitrary prompt composition UI

Start with checked-in manifests and deterministic runtime behavior.

## Bottom Line

`palamedes` is not skill-based today, and that is correct.

The right move is:

- keep Palamedes contract-first
- make `palamedes-agents` skill-aware
- treat skills as runtime behavior bundles above the capability boundary
- track desired vs actual skill injection explicitly

That preserves the kernel boundary while giving the orchestration repo a clean, scalable skill model.
