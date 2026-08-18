# Planning handoff proof — Gahyeon 001

## Result

- Blind preference: planning brief 3, mission only 0, tie 0
- Planning-brief downstream plan: 5.0 / 5 from all three reviewers
- Mission-only downstream plan: 4.2, 4.4, 4.4 / 5
- Mean reconstruction burden: planning brief 1.0, mission only 2.0
- The bounded model-review calibration claim passed.
- No implementation or beneficiary-outcome claim passed.

Both conditions preserved the mission and chose the gated packaged Unreal vertical slice. The
planning-brief condition won because it more clearly separated contract, prerequisite readiness,
packaged-boundary proof, loop composition, adversarial verification, and evidence review. It also
specified resource ceilings, approval boundaries, evidence integrity, reviewer responsibility,
diagnostic allowances, and stop or rescope dispositions more completely.

The mission-only planner was already strong. Its main defect was a mild sequencing ambiguity: it
partly placed repeated packaged-build production inside the availability gate and left more
evidence governance, acquisition constraints, resource controls, approval mechanics, and review
disposition for the downstream planner to reconstruct.

## Compute tradeoff

| Path | Calls before review | Input tokens | Output tokens |
| --- | ---: | ---: | ---: |
| Mission → planner | 1 | 25,485 | 3,282 |
| Mission → brief architect/reviewer → planner | 3 | 92,201 | 17,890 |

The complete planning-brief path used about 3.62 times the input tokens and 5.45 times the output
tokens before blind review. Considering only the final identical planner call, the brief condition
used 31,481 input tokens versus 25,485 for mission-only, a 1.24 ratio.

The observed gain is therefore real within this model evaluation but not free. A future routing
policy should reserve the full brief for high-uncertainty, high-coordination, or costly plans rather
than generate it for every decision.

## Evidence limits

- This is one repeated Gahyeon case, not an unfamiliar holdout.
- The mission, planning brief, planners, and reviewers share a configured model family.
- Review sessions were fresh and origin-blinded, but their judgments may be correlated.
- More treatment compute and context were intentionally used and fully reported.
- No external owner confirmed relevance or approved the plan.
- No Unreal work was executed and no user or beneficiary outcome was measured.
- `claim_demonstrated: true` in `score.json` means only that the bounded model-review preference
  gate passed; it is not an Inventor or real-outcome proof.

## Next proof

Use at least three unfamiliar owner-confirmed missions. Randomize mission-only versus planning-brief
handoffs to identical independent planners, measure clarification questions and human correction
time before execution, then compare implementation defects, stop-rule timing, and beneficiary
outcomes under predeclared budgets.
