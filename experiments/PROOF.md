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
  --evidence "<timestamped evidence location>"
```

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
