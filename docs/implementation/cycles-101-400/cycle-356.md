# Improvement Cycle 356

## Topic

Type planner challenges at the mission boundary.

## Deficiency

Free-form planner objections blur fundamentally different problems. A hard
constraint, unclear clause, causal counterclaim, portfolio resource collision,
and meaning-preserving mechanism alternative require different evidence and
different governance responses.

## Improvement

Added `validate_typed_planner_mission_challenge` and an experimental schema.

Every challenge is exactly one of infeasibility, ambiguity, causal objection,
resource conflict, or alternative mechanism. Infeasibility includes the tested
alternative; ambiguity includes competing interpretations without a planner
default; causal objection includes a countermechanism and discriminating test;
resource conflict includes the competing commitment and allocation authority;
an alternative mechanism includes comparative evidence and a meaning
preservation test. Untyped objections and implementation before resolution are
forbidden.

## Scope boundary

Cycle 356 gives challenges evidence-bearing types. Cycle 357 will decide which
typed challenges affect purpose and therefore require a Palamedes answer while
leaving implementation choices with the planner.

## Verification

- focused mission tests: 1029 passed
- schema JSON parse: 253 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A planner cannot hide a mission-boundary problem inside a generic objection;
the challenge type determines the evidence it must carry.
