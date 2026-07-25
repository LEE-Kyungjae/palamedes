# Palamedes Pre-Planner Contract

Status: product hypothesis

## Position

Palamedes owns the cognitive layer before planning.

```text
signals -> Palamedes -> mission contract -> planner -> tasks -> implementation
   ^                                                         |
   └---------------- outcomes and consequences --------------┘
```

A planner answers: “How should this goal be achieved?”

Palamedes answers the prior questions:

- What in the world deserves attention?
- Which unmet desire, contradiction, or possibility matters?
- What goal is worth creating now?
- Why this goal rather than the available alternatives?
- What must remain true while pursuing it?
- What evidence should change or terminate the mission?

## Required inputs

Palamedes may use:

- environmental and operational signals;
- accumulated project and owner history;
- a revisable value constitution containing principles, learned preferences,
  prohibitions, uncertainties, beneficiary representation, precedent, and
  authority limits;
- reference lineages, failures, anomalies, and remote mechanisms;
- capabilities, resources, obligations, and opportunity costs;
- downstream outcomes from planners and implementers.

It must distinguish observed facts, inferred relations, transferred mechanisms,
simulations, preferences, and commitments.

## Mission contract

The output delivered to a planner must contain:

1. `situation`: what changed or became visible;
2. `meaning`: why the situation matters;
3. `mission`: the outcome now worth pursuing;
4. `beneficiary`: whose condition should change;
5. `desire_model`: the need, tension, or possibility being served;
6. `thesis`: why this intervention could create the outcome;
7. `alternatives_rejected`: serious competing missions and rejection reasons;
8. `non_goals`: attractive work that must not consume the mission;
9. `success_and_harm`: desired consequences and unacceptable side effects;
10. `disconfirmation`: evidence that should revise or stop the mission;
11. `authority`: what downstream agents may decide autonomously;
12. `escalation_boundary`: only conflicts outside delegated authority;
13. `lineage`: observations, references, and view transitions that produced the
    mission;
14. `review_trigger`: events that require Palamedes to reconsider what is worth
    doing.
15. `value_basis`: which constitutional principles, beneficiary claims, learned
    preferences, and unresolved value conflicts support the selection;
16. `resource_renewal`: how the mission sustains or explicitly consumes the
    resources required to continue;
17. `anti_entrenchment`: why Palamedes itself is necessary and what simpler
    mechanism or evidence should replace it.

The mission contract is not a task list or implementation plan.

## Autonomous cognition loop

1. Observe changes, anomalies, failures, desires, and unused capabilities.
2. Maintain multiple interpretations before selecting a problem frame.
3. Search close ancestry, opposition, failures, and remote mechanisms.
4. Generate competing missions independently.
5. Attack proxy risks, imitation, owner-bias amplification, and hidden harms.
6. Compare missions by consequence, option value, information gain, feasibility,
   reversibility, and constitutional fit.
7. Select, defer, or reject without requiring routine human approval.
8. Issue a mission contract to a planner.
9. Monitor implementation outcomes rather than task activity alone.
10. Revise the mission, not merely the plan, when its meaning or value changes.

## Operational state

The first vertical slice should preserve these objects separately:

- `signals`: observed deviations with source incentives, expected baseline,
  affected entities, uncertainty, and coverage blind spots;
- `constitution_state`: hard prohibitions, defeasible principles, learned
  preferences, beneficiary representation, precedents, conflicts, and authority;
- `causal_sketches`: competing interpretations with mechanisms, predictions, and
  observations that would make each interpretation lose;
- `mission_candidates`: independently generated beneficiary-condition changes
  with causal theses, failure conditions, and resource implications;
- `mission_tournament`: dominance relations, disqualifications, unresolved
  tradeoffs, decisive assumptions, exploration budgets, and reversal triggers;
- `mission_contracts`: versioned handoffs to planners;
- `mission_frontier`: unresolved assumptions and wake triggers;
- `mission_outcomes`: observed consequences and separated attribution across
  mission, planning, implementation, environment, and measurement.

The runtime wakes on a value-relevant deviation, forecast miss, authority
conflict, expiring opportunity, scheduled mission review, or downstream boundary
return. Each wake selects the least sufficient cognitive operation rather than
rerunning the entire pipeline.

## Mission competition

Candidate missions should be formed independently from different evidence
slices before they share a common comparison context. Palamedes should not force
all missions into one scalar score. It may preserve a partial ordering when
plural values remain incomparable, then choose a reversible or
information-producing intervention to resolve the relevant uncertainty.

Selection must expose:

- beneficiary condition and representation confidence;
- constitutional fit and unresolved value conflict;
- causal thesis and early disconfirmation;
- upside, downside, reversibility, and option value;
- exploration budget and displaced alternatives;
- resource-renewal mechanism;
- self-benefit or institutional-expansion conflicts.

## Anti-entrenchment

Palamedes must treat its own expansion and continued use as adversarial
hypotheses. Self-improvement is justified only by an external mission and must
remain independently bounded. If a planner, a simpler agent, or a static process
can originate an equally strong mission from the same signal stream, Palamedes
has added ceremony rather than upstream intelligence.

## Human boundary

Palamedes is designed to reduce the final area where a human currently originates
purpose for capable execution agents. Human participation is an exception path,
not the normal thinking loop.

Escalation remains necessary when:

- delegated constitutional principles conflict and no precedence exists;
- the required authority was never granted;
- an irreversible obligation affects people or systems outside the mandate;
- evidence indicates the preference model is materially wrong and no safe
  correction can be inferred.

This boundary exists to make delegation coherent, not to return ordinary product
judgment to the human.

## First proof

The first proof should compare missions, not implementation plans.

Given the same evolving signal stream, compare:

- a human-originated mission;
- a strong general agent prompted once;
- Palamedes operating over repeated upstream cognition cycles.

Before downstream execution, freeze each mission contract. After execution,
evaluate:

- whether it noticed a consequential opportunity others missed;
- whether its mission remained coherent under planning;
- whether its disconfirmation criteria detected failure early;
- whether downstream work changed the beneficiary as intended;
- whether it originated a better subsequent mission from the outcome;
- how much human upstream cognitive labor was actually retired.

The claim fails if Palamedes merely produces more elaborate rationales, imitates
the owner's known preferences, or delegates a generic mission that planners
could have inferred themselves.

The minimum comparison should use one evolving signal stream containing at least
two plausible beneficiary interpretations and three serious mission candidates.
Freeze constitution and authority before exposure. Compare equal-information
human, one-shot-agent, and Palamedes conditions, then hand blinded mission
contracts to identical planners. Measure upstream human labor, mission quality,
planner reconstruction burden, disconfirmation quality, beneficiary outcome,
proxy harm, and whether a subsequent mission improves from returned consequences.

## Bounded implementation order

The first implementation should stop after these five artifacts:

1. JSON schemas and validators for signal, constitution state, causal sketch,
   mission candidate, tournament, mission contract, frontier, and outcome;
2. intent-specific state commands with freezing, provenance, fingerprint, and
   revision invariants;
3. a provider-neutral `MissionCycle` that separates interpreter, independent
   inventor, adversary, selector, and outcome-analysis roles;
4. one sequential replay case containing beneficiary ambiguity, manipulated
   urgency, and a tempting Palamedes self-expansion mission;
5. a traceable compiler from selected mission contract to the existing planner
   goal envelope, plus acknowledgment-based semantic-loss measurement.

Semantic judgment remains model-backed. Deterministic code owns schema,
independence boundaries, eligibility, hard constitutional prohibitions,
dominance under shared assumptions, idempotency, lineage, authority, and routing.
On provider failure, Palamedes defers judgment; it does not substitute a
rule-based purpose score.
