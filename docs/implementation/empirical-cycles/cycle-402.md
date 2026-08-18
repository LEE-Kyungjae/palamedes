# Empirical Improvement Cycle 402

## Topic

Expand a selected mission into a scale-adaptive planning brief without collapsing mission,
planning, and execution authority.

## Deficiency

The Gahyeon case-zero result selected a defensible direction and a cheap prerequisite gate, but it
did not constitute a new-service or content construction plan. It lacked a user experience
contract, alternatives, concrete components, dependency closure, phased outputs, resource
envelope, and effect lifecycle. A model reviewer could prefer the answer while downstream builders
still had to originate most of the plan.

## Improvement

Added `validate_scale_adaptive_planning_brief` and an experimental schema. The validator chooses
required resolution from both plan scale and planning stage:

- direction may keep concepts and implementation detail unresolved;
- content, service, and platform concepts require an experience contract, alternatives,
  components, dependencies, and an effect register;
- approval and delivery briefs additionally require phases and a resource envelope;
- observed or decided claims require evidence, while assumptions and unresolved items require a
  validation probe;
- components use `requires` and `provides`, inspired by Cordis spatial composability;
- effects distinguish rollback, compensation, and separately approved irreversibility, adapting
  Cordis temporal composability to real-world planning.

## Scope boundary

Cycle 402 adds a deterministic contract and one realistic Gahyeon fixture. It does not yet add a
model-backed planning-brief generator, execute the plan, or import Cordis as a dependency. The
planning brief preserves mission semantics and explicitly issues no execution authority.

## Resulting invariant

A large-plan answer cannot pass as an approval-ready planning brief merely because it names a
direction and a next probe. It must expose the experience, alternatives, components, dependency
closure, effects, phases, resources, and decision gates appropriate to its maturity without
pretending unresolved facts are decided.
