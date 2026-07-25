# proof-002 result

Status: mission-quality gate passed; one attributable downstream choice
recorded; owner-labor gate pending; bounded claim not yet demonstrated.

## Frozen comparison

- Three real repository cases: Palamedes self-hosting, Gahyeonbot voice-loop
  sequencing, and Termi agent-control boundaries.
- Both conditions received the same frozen information packet and configured
  Codex model.
- The baseline used one call per case. Palamedes used four role calls per case.
- Inputs and repository revisions were committed before generation.
- Mission origin was hidden during review.

## Result

| Case | Palamedes votes | Baseline votes | Majority |
| --- | ---: | ---: | --- |
| Palamedes self-hosting | 3 | 0 | Palamedes |
| Gahyeonbot voice loop | 2 | 1 | Palamedes |
| Termi agent control | 3 | 0 | Palamedes |
| **Total** | **8** | **1** | **3/3 cases** |

All reviewers were fresh-session Codex model reviewers using the same frozen
blind packet. They were origin-blinded, but they are neither independent human
reviewers nor different model families.

## Cost

| Condition | Calls | Input tokens | Output tokens | Reasoning tokens |
| --- | ---: | ---: | ---: | ---: |
| Baseline generation | 3 | 69,756 | 2,141 | 205 |
| Palamedes generation | 12 | 297,173 | 11,329 | 325 |
| Blind review | 9 | 171,470 | 3,221 | 1,183 |

Palamedes used 4.26 times the baseline input tokens during generation. The run
therefore establishes an initial quality advantage for the tested operating
configurations, not an equal-compute or cost-adjusted advantage.

## Gate interpretation

- `mission_quality_gate_passed=true`: passed.
- `attributable_outcomes=1`: the selected Palamedes mission caused the
  `proof-003` equal-call comparator to be implemented, preregistered, executed,
  and published before feature expansion. The evidence chain is commits
  `25bcb41`, `0396f13`, and `74e89f8`.
- `outcome_gate_passed=false`: no owner-attested upstream labor retirement has
  been recorded.
- `claim_demonstrated=false`: the preregistered bounded product claim remains
  unproven until both gates pass.

Machine-readable evidence is in [`score.json`](score.json), with the frozen
inputs, raw condition outputs, blind packet, answer key, and all reviewer
records stored beside it.
