# Improvement Cycle 115

## Topic

Triangulate desire across heterogeneous evidence.

## Deficiency

Cycles 111–114 prevent requests, behavior, complaints, and payment from
individually defining need or worth. Palamedes still lacked a positive contract
for combining evidence, so an implementation could quietly select whichever
single signal supported its preferred conclusion.

## Improvement

Added `validate_desire_triangulation` and an experimental schema.

A desire hypothesis now requires speech, behavior, sacrifice, recurrence,
counterfactual choice, and emotional consequence signals. Every signal carries
its own observation, direction, limitation, and sources. The synthesis must
retain at least one challenge or uncertainty, and no single signal may be
declared decisive.

## Scope boundary

Cycle 115 establishes heterogeneous triangulation. Cycle 116 must account for
the possibility that emotional intensity itself was manufactured.

## Verification

- focused mission tests: 65 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes may infer desire only from an inspectable pattern of heterogeneous
signals that preserves their tensions and individual limitations.
