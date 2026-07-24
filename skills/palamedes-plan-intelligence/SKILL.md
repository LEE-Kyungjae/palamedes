---
name: palamedes-plan-intelligence
description: Use when the user wants plan-only collaboration in the Palamedes repo, especially for long-horizon planning, idea discovery from zero, insight generation, and improving planning quality before any task/implementation work.
---

# Palamedes Plan Intelligence

## Overview

This skill runs Palamedes as a plan-only copilot. It improves direction quality, insight depth, and long-horizon planning structure using the local `palamedes.py` CLI.

Use this skill when the user asks to:

- build or refine plans before execution
- find ideas from a zero-idea state
- generate broader viewpoints or references
- set a planning horizon (weeks/months), review cadence, and milestone phases
- improve Palamedes QA coverage for insight axes

Do not use this skill for implementation workflows, coding tasks after planning, deployment, or debugging app runtime issues.

## Workflow

1. Baseline
- Run `python3 palamedes.py show`
- Run `python3 palamedes.py qa`

2. Horizon setup (required for long-horizon planning)
- Ensure `planning_horizon`, `review_cadence`, `phase_plan` are set
- Example:
```bash
python3 palamedes.py plan \
  --planning-horizon "12 weeks" \
  --review-cadence "weekly" \
  --phase-plan "phase1 framing,phase2 validation,phase3 refinement"
```

3. Insight expansion
- Generate viewpoint expansion and apply to the current plan:
```bash
python3 palamedes.py insight \
  --topic "<topic>" \
  --references "<success_case,fail_case,counter_view>" \
  --apply
```
- Focus on broadening perspective before deciding.

4. QA-driven refinement
- Run `python3 palamedes.py qa`
- If not passing, fill missing fields using `plan`/`replan` arguments, especially:
  - 8 insight axes:
    - `direction_insights`
    - `market_insights`
    - `timing_insights`
    - `differentiation_insights`
    - `monetization_insights`
    - `constraint_insights`
    - `risk_signal_insights`
    - `evolution_insights`
  - horizon fields:
    - `planning_horizon`
    - `review_cadence`
    - `phase_plan`

5. Return concise planning summary
- Direction statement
- Top risks and early signals
- Horizon and review cadence
- 1-3 next planning questions (not implementation tasks)

6. Cycle review for long-term co-work
- Run:
```bash
python3 palamedes.py review --period "<week-or-month>" --signals "<s1,s2>" --apply
```
- Use output recommendations and next questions to decide the next planning cycle.

## Command Reference

- Baseline: `python3 palamedes.py show && python3 palamedes.py qa`
- Idea generation: `python3 palamedes.py ideate --profile "<profile>" --interests "<a,b,c>" --count 5`
- Plan update: `python3 palamedes.py plan --goal "<goal>" --success-metric "<metric>" --deadline "YYYY-MM-DD"`
- Insight pack: `python3 palamedes.py insight --topic "<topic>" --references "<r1,r2,r3>" --apply`
- Evidence: `python3 palamedes.py evidence --claim "<claim>" --source "<source>" --confidence 70 --axis market`
- Hypothesis: `python3 palamedes.py hypothesis --hypothesis "<statement>" --metric "<metric>" --target "<target>" --window "<window>"`
- Replan update: `python3 palamedes.py replan --evidence "<evidence>" --direction-insight "<insight>"`
- Cycle review: `python3 palamedes.py review --period "<cycle>" --signals "<s1,s2>" --apply`

See [references/prompt-templates.md](references/prompt-templates.md) for ready-to-use invocation prompts.

## Output Rules

- Keep focus on planning decisions and insight quality.
- Do not drift into coding implementation plans unless explicitly requested.
- Prefer evidence-backed and counter-viewpoint-inclusive insight generation.
