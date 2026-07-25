# Improvement Cycle 144

## Topic

Resolve weak authority analogies through safe sandbox evidence.

## Deficiency

Cycle 143 prevents weak analogies from silently expanding authority. Escalating
every uncertain case, however, recreates human dependence even when a
consequence-free simulation could resolve the material difference.

## Improvement

Added `validate_authority_sandbox_probe` and an experimental schema.

The probe uses synthetic inputs inside an explicit sandbox, with no external
communication, real affected parties, persistent effect, or commitment. It is
resource-bounded and reversible, states distinguishing outcomes and an analogy
update rule, and stops before crossing the sandbox boundary.

## Scope boundary

Cycle 144 permits internal evidence gathering. Cycle 145 must distinguish
private drafts and simulations from publication, which creates commitment by
being seen.

## Verification

- focused mission tests: 181 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can reduce authority uncertainty autonomously only through isolated
actions that cannot themselves create the consequence under dispute.
