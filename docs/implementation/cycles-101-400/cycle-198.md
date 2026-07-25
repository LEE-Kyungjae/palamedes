# Improvement Cycle 198

## Topic

Prove one originated mission under evolving adversarial signals.

## Deficiency

The first implementation could expand into an entire autonomous company before
showing that Palamedes can originate even one mission without hidden human goal
injection and defend it against serious criticism.

## Improvement

Added `validate_single_mission_adversarial_proof` and an experimental schema.

The proof is limited to exactly one mission and explicitly excludes company-wide
automation and human goal injection. At least two sequential signal events must
be linked to mission origin. The mission survives only when pre-registered
criteria are met under causal-thesis, constitutional-fit, and replaceability
attacks.

## Scope boundary

Cycle 198 defines the first bounded proof unit. Cycle 199 will define success as
retired human upstream labor without proxy harm, hidden authority, or empty
rationales.

## Verification

- focused mission tests: 397 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes must first originate and defend one worthwhile mission from changing
reality before claiming to automate a company.
