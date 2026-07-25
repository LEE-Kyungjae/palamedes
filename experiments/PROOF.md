# Palamedes Proof Program

This program tests a narrow claim:

> Given the same frozen project information, Palamedes produces a more useful
> mission than a one-shot general agent and retires material upstream framing
> labor.

It does not treat schema validity, test count, prose quality, repository stars,
or successful implementation as proof of better judgment. It also does not
claim that Palamedes guarantees startup success.

## Preregistered gate

The authoritative portfolio is [`proof-portfolio.json`](proof-portfolio.json).
It requires:

- three real projects with frozen revisions and artifact hashes;
- the same bounded information packet and Codex model in both conditions;
- a fresh one-call general-agent baseline;
- a four-call Palamedes interpreter/inventor/adversary/selector condition;
- explicit reporting of the compute asymmetry;
- origin-blinded scoring on problem framing, non-genericity, evidence use,
  falsifiability, and decision usefulness;
- Palamedes preference in at least two of three cases;
- at least one observed consequential choice attributable to a mission;
- at least one owner record showing material upstream framing labor retired.

Mission preference and outcome evidence are separate gates. Passing the blind
quality comparison without a real choice and labor record leaves the product
claim unproven.

## Reproduce

Freeze a new run before generating either condition:

```bash
python3 palamedes_proof.py prepare \
  --run-id proof-002 \
  --run-root experiments/proof-runs
```

Commit the manifest and information packets before continuing. Then generate
both conditions:

```bash
python3 palamedes_proof.py generate \
  --run experiments/proof-runs/proof-002 \
  --condition baseline

python3 palamedes_proof.py generate \
  --run experiments/proof-runs/proof-002 \
  --condition palamedes
```

Create the blinded packet and keep the answer key separate:

```bash
python3 palamedes_proof.py blind \
  --run experiments/proof-runs/proof-002 \
  --seed "<unpublished-random-seed>"
```

Collect one or more reviews. The built-in Codex reviewer is useful as a
fresh-session, origin-blinded first pass, but must be identified as model review
rather than independent human validation:

```bash
python3 palamedes_proof.py review \
  --run experiments/proof-runs/proof-002 \
  --reviewer-id codex-blind-1
```

Record observed outcomes only after a real decision:

```bash
python3 palamedes_proof.py outcome \
  --run experiments/proof-runs/proof-002 \
  --case-id <case-id> \
  --selected-system palamedes \
  --observed-choice "<choice that actually occurred>" \
  --attributable-decision \
  --owner-seconds-without <counterfactual-seconds> \
  --owner-seconds-with <observed-seconds> \
  --owner-attestation "<owner's explicit estimate in their own words>" \
  --evidence "<timestamped evidence location>"
```

Do not infer or backfill the owner's counterfactual time. The outcome gate
counts labor retirement only when the record contains an explicit owner
attestation and timestamped evidence.

Finally:

```bash
python3 palamedes_proof.py score \
  --run experiments/proof-runs/proof-002
```

## Interpretation

- `mission_quality_gate_passed=true` means only that the preregistered blinded
  mission comparison passed.
- `outcome_gate_passed=true` means a consequential choice and labor retirement
  were actually recorded.
- `claim_demonstrated=true` requires both.
- A demonstrated result is limited to this three-case portfolio. It does not
  establish universal model superiority or business-success causality.

`proof-001` is the first frozen run. Its inputs were committed before condition
generation so later results cannot change its initial information.

## Current evidence

[`proof-002`](proof-runs/proof-002/RESULT.md) is the first completed mission
quality run. Three fresh-session Codex reviewers evaluated three origin-blinded
cases:

- Palamedes received 8 of 9 preference votes and won all three case majorities.
- Two cases were unanimous; the Gahyeonbot case split 2–1.
- Palamedes generation used 297,173 input tokens versus the baseline's 69,756,
  a 4.26x ratio.
- The quality gate passed, but the outcome gate did not. No attributable choice
  or owner-attested labor retirement has been recorded.

This is repeatable model-review evidence for mission quality under unequal
compute. It is not yet cost-adjusted superiority, independent human validation,
or proof of improved startup outcomes.

The preregistered [`proof-cost-portfolio.json`](proof-cost-portfolio.json)
addresses the largest compute objection with a stronger four-call comparator.
Its `tournament` condition generates three independent missions through
different product lenses and spends the fourth call selecting among them.
Palamedes also receives four calls. Token and latency differences remain
measured rather than assumed equal.

That comparison is now complete as
[`proof-003`](proof-runs/proof-003/RESULT.md):

- both conditions used 12 generation calls across the three cases;
- Palamedes used 297,332 input tokens and the tournament used 284,496, a
  1.045x ratio;
- Palamedes received 7 of 9 blinded model-review votes and won two of three
  case majorities;
- the preregistered equal-call mission-quality claim passed;
- outcome evidence was outside this narrow run and is explicitly marked not
  applicable, rather than passed.
