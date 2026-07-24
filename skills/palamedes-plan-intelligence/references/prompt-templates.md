# Prompt Templates

Use these when invoking `$palamedes-plan-intelligence`.

## Codex Prompt

Use `$palamedes-plan-intelligence` in this repo and keep the work plan-only.
Run `python3 palamedes.py show` and `python3 palamedes.py qa` first.
Then improve long-horizon plan quality using:
- `planning_horizon`, `review_cadence`, `phase_plan`
- 8 insight axes coverage
Add structured evidence and hypothesis entries when signals are weak:
- `python3 palamedes.py evidence --claim "<claim>" --source "<source>" --confidence 70 --axis <axis>`
- `python3 palamedes.py hypothesis --hypothesis "<statement>" --metric "<metric>" --target "<target>" --window "<window>"`
Generate and apply an insight pack if needed:
`python3 palamedes.py insight --topic "<topic>" --references "<r1,r2,r3>" --apply`
Close each cycle with:
`python3 palamedes.py review --period "<week-or-month>" --signals "<s1,s2>" --apply`
Return only planning summary, risk signals, and next planning questions.

## Claude Prompt

Use `$palamedes-plan-intelligence` for planning only.
Do not provide implementation steps.
Start with `show` and `qa`, then improve plan quality and long-horizon structure.
If insight depth is low, run the insight command and apply results.
Then run cycle review with period and signals to produce replan questions.
Finish with: direction statement, horizon/cadence, top risks, and unresolved planning questions.
