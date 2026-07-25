# proof-003 result

Status: the preregistered same-model, equal-call mission-quality claim passed.
Downstream outcomes were not part of this narrow run.

## Frozen comparison

- Three real repository cases were frozen and committed before generation.
- Both conditions received the same information packets and configured Codex
  model.
- The strong comparator generated three independent missions through different
  product lenses and spent a fourth call selecting one.
- Palamedes used interpreter, inventor, adversary, and selector calls.
- Both conditions therefore used four calls per case and 12 calls in total.
- A/B origins were hidden from three fresh-session Codex reviewers.

## Result

| Case | Palamedes votes | Tournament votes | Majority |
| --- | ---: | ---: | --- |
| Palamedes self-hosting | 1 | 2 | Tournament |
| Gahyeonbot voice loop | 3 | 0 | Palamedes |
| Termi agent control | 3 | 0 | Palamedes |
| **Total** | **7** | **2** | **Palamedes 2/3 cases** |

The preregistered threshold required Palamedes to win at least two of three
case majorities with three reviews per case. It passed exactly that gate.
The self-hosting loss is retained: two reviewers preferred moving directly to
a live downstream trial over another mechanism-ablation step.

## Cost

| Condition | Calls | Input tokens | Output tokens | Reasoning tokens |
| --- | ---: | ---: | ---: | ---: |
| Strong tournament | 12 | 284,496 | 8,120 | 447 |
| Palamedes | 12 | 297,332 | 11,728 | 396 |
| Blind review | 9 | 171,370 | 3,297 | 1,171 |

Palamedes used 1.045 times the tournament's input tokens. This removes most of
the 4.26x input-cost asymmetry in `proof-002`, although exact token and output
costs were not equal.

## Claim boundary

This run demonstrates the narrow claim that, on these three frozen cases and
with the same configured model and call count, the Palamedes role sequence
outperformed a strong independent-candidate tournament under blinded model
review.

It does not establish:

- independent human preference;
- superiority across model families or unseen domains;
- equal-token or monetary-cost superiority;
- attributable downstream benefit or startup success;
- owner labor retirement.

Machine-readable evidence is in [`score.json`](score.json). Frozen inputs, raw
condition outputs, blind packet, answer key, and reviewer records are stored
beside it.
