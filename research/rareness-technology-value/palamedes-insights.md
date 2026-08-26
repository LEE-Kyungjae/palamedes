# Palamedes research synthesis: rareness and recombinant value

## Bottom line

The strongest transferable principle is not "reward rare ideas." It is:

> Preserve a legible, causally grounded core while introducing a small number
> of genuinely atypical relations, then price the cost of understanding,
> complement discovery, integration, and disconfirmation before promotion.

Palamedes already contains important safeguards that agree with this principle:

- discovery scores novelty separately from potential value, uncertainty, and
  scope risk;
- anomaly detection does not assign meaning or infer harm before investigation;
- consequence eligibility and causal coherence precede novelty evaluation;
- known components are permitted when their relation or activation condition
  creates an irreducible outcome;
- novelty cannot override an otherwise ineligible mission.

The main missing layer is an operational model of *recombinant position*.
Current contracts can require a novelty score and rationale without measuring
whether a candidate has a conventional core, an atypical tail, accessible
complements, or an absorbable distance from the system's actual knowledge base.

## What the focal paper contributes

Lee, Jung, and Park (2023) model technology rareness as a relative position in
a technology space, combining novelty and conventionality. Their argument is a
trade-off:

1. rareness can increase recombinant potential;
2. rareness also increases the cost of understanding the adopted technology;
3. rareness increases the cost of finding complementary technologies;
4. consequently, reported technology value follows an inverted-U relationship;
5. the curve is steeper when the focal technology rests on more local knowledge;
6. the curve is flatter when it embeds more mature knowledge.

This is observational evidence from U.S. firm nanotechnology patents. Value is
subsequent technological impact, not user utility, welfare, revenue, or mission
quality. The paper therefore supports a mechanism hypothesis, not a universal
scoring function for Palamedes.

## What the related papers add

### Fleming (2001): model variance, not only expected value

Fleming studies 17,264 U.S. patents granted in May and June 1990 and uses future
patent citations as a usefulness proxy. Patent subclasses proxy components.
Recent/frequent component and combination use proxy familiarity, while
cumulative exact-combination use proxies exhaustion.

The transferable result is distributional: unfamiliar components and
combinations produce lower usefulness on average but greater variability, so
they increase both failure and breakthrough potential. Familiar combinations
reduce uncertainty; very familiar components have a nonmonotonic relationship
with uncertainty. The paper explicitly warns that patents omit unpatented
invention, subclass combinations are imperfect component proxies, and learning,
exhaustion, and technology life cycles cannot be cleanly separated.

**Palamedes implication:** candidate evaluation should retain both expected
value and outcome dispersion. A high-variance candidate may deserve a bounded
probe, not promotion or rejection based only on its mean score.

### Uzzi et al. (2013): separate the conventional core from the novel tail

Uzzi and colleagues analyze 17.9 million Web of Science papers. They compare
observed co-cited journal pairs with randomized citation networks, using a
paper's median pair z-score for its conventional core and its 10th-percentile
z-score for its atypical tail.

High-impact work is not globally unconventional. Papers combining high median
conventionality with high tail novelty had a 9.11% hit rate against a 5%
background definition of a hit. Peak impact occurred around the 85th-95th
percentile of median conventionality. This is an association in scholarly
citations, not proof that this exact mix causes mission value.

**Palamedes implication:** replace one-dimensional novelty with two independent
diagnostics: `conventional_core_strength` and `atypical_relation_tail`. A
candidate can and often should be high on both.

### Stuart & Podolny (1996): locality is relational and time-dependent

Stuart and Podolny map the technological positions of the ten largest Japanese
semiconductor producers from 1982 to 1992 using patent relationships. Their
central methodological point is that local search is meaningful only relative
to a wider, simultaneously changing technological landscape. A firm's position
can change because competitors move, even if the firm does not.

**Palamedes implication:** `local_knowledge` cannot be a static label or simple
embedding distance. It needs a dated comparison population, provenance, and a
record of which capabilities are actually available to the current host.

### Capaldo et al. (2017): maturity has its own optimum and contingencies

Using 5,575 biotechnology patents, this paper reports an inverted-U relationship
between knowledge maturity and scientific value. Moderate maturity can improve
reliability and applicability; excessive maturity can bring obsolescence and
retrieval/application problems. Technological distance, geographical distance,
and industry adoption alter the relationship in different ways.

**Palamedes implication:** do not collapse maturity into familiarity. Track at
least evidence age, last successful reuse, current applicability, adoption
saturation, and obsolescence risk.

### Fontana et al. (2020): novelty metrics can measure the wrong construct

This paper challenges prominent recombination metrics. In its physics-paper
sample, atypical-combination and first-combination measures overlap with
interdisciplinarity or struggle to distinguish novel from non-novel work.

**Palamedes implication:** a distance score is not construct validity. Every
novelty claim should survive multiple tests: relation rarity, structural delta,
baseline reducibility, semantic/domain distance, and human judgment. Report
disagreement among these measures instead of averaging it away.

## Concrete gaps in the current Palamedes design

### 1. A scalar novelty score hides useful structure

`persist_discoveries` accepts `novelty_score`, while the invention adversary
performs qualitative novelty tests. Neither expresses the distribution of
familiar versus unusual relations that Uzzi et al. show is informative.

**Add to evaluation, not necessarily selection:**

```json
{
  "recombinant_profile": {
    "known_components": [],
    "conventional_core_strength": 0.0,
    "atypical_relations": [],
    "atypical_tail_strength": 0.0,
    "comparison_population_id": "...",
    "comparison_as_of": "..."
  }
}
```

### 2. Rareness is not conditioned on absorption capacity

The system records grounding and causal coherence but does not explicitly price
whether the host can understand and absorb the proposed combination.

Track:

- distance from demonstrated host capabilities;
- missing concepts and expected learning effort;
- provenance quality and explanation burden;
- whether a knowledgeable human or tool can validate the relation.

### 3. Complement search and integration costs are implicit

The focal paper's negative mechanism is partly the difficulty of finding and
integrating complements. Palamedes has system complexity, operator burden, and
irreversibility checks, but these occur at a broader mission level.

Add candidate-level evidence for:

- required complementary capabilities;
- availability and compatibility of each complement;
- integration dependencies and coordination owners;
- smallest end-to-end integration probe;
- failure localization: whether a failed probe tests the idea or merely a
  missing complement.

### 4. Expected value and variance are not a portfolio

The discovery record separately captures value and uncertainty, which is a good
start, but it does not state how uncertainty changes treatment.

Use three possible dispositions:

- high expected value, low uncertainty: normal evidence progression;
- plausible value, high upside and high variance: small bounded probe;
- high novelty with no interpretable success/failure signal: defer until a
  discriminating probe exists.

### 5. Locality and maturity lack time-indexed baselines

Grounding IDs prove that knowledge was cited, not that it is local, current,
absorbed, or mature. A useful record would distinguish:

- `host_familiarity`: demonstrated internal competence;
- `ecosystem_conventionality`: frequency in the relevant external population;
- `knowledge_maturity`: age plus accumulated validation;
- `adoption_saturation`: remaining headroom for differentiated reuse;
- `obsolescence_risk`: likelihood that old evidence no longer applies.

### 6. There is no calibration dataset for novelty claims

The code has strong semantic contracts but no evidence here that its novelty
scores are calibrated against human comparisons or later outcomes.

Create an evaluation set containing:

- obvious restatements and generic bundles;
- conventional-core/novel-tail candidates;
- globally strange but unusable candidates;
- distant candidates made feasible by a newly available complement;
- mature knowledge reused in a genuinely new context;
- false novelty caused by missing retrieval;
- false familiarity caused by an overly broad comparison population.

## Proposed research-to-product experiment

Do not encode the paper's inverted-U as a hard reward curve yet. First run an
offline comparison:

1. sample historical Palamedes candidates and preserve their original outcomes;
2. blind reviewers score conventional core, atypical tail, host locality,
   maturity, complement availability, comprehension cost, and integration cost;
3. compare these dimensions with the current novelty/value/uncertainty scores;
4. measure inter-rater reliability and disagreement between novelty metrics;
5. test whether the added dimensions predict human preservation decisions,
   successful bounded probes, and later realized usefulness;
6. fit no nonlinear optimum unless the Palamedes-specific data supports one;
7. keep rights, harm, authority, and causal gates outside any empirical value
   score so measured impact cannot override constitutional constraints.

## Priority order

1. **Decompose novelty:** conventional core versus atypical relational tail.
2. **Make complements explicit:** availability, compatibility, and integration
   cost at candidate level.
3. **Time-index the comparison frame:** host capability, ecosystem baseline,
   maturity, adoption, and obsolescence.
4. **Use uncertainty operationally:** map high variance to bounded probes.
5. **Calibrate on Palamedes outcomes:** do not import patent citation optima.
6. **Triangulate novelty measures:** preserve metric disagreement as evidence.

## Initial implementation

The first non-authorizing diagnostic contract is implemented in
`palamedes_mission/_18_recombinant_value.py` as
`validate_recombinant_value_profile`.

It requires:

- a conventional core and explicit atypical component relations;
- five separate novelty measures and preservation of material disagreement;
- a dated comparison population and host-capability snapshot;
- comprehension cost and missing knowledge;
- maturity, adoption saturation, and obsolescence risk;
- complement availability, compatibility, ownership, and integration cost;
- expected value and outcome variance with an explicit uncertainty treatment;
- reversible success/failure signals for a bounded probe.

The profile cannot authorize a mission, bypass constitutional gates, use
citation impact as beneficiary value, or hardcode the patent literature's
inverted-U relationship. This is an instrumentation layer for later calibration,
not a new mission-selection score.

The grounded evaluator now adds three further constraints:

- every evidence ID, comparison population, and host-capability snapshot must
  resolve in the supplied registry and must not postdate the evaluation;
- every dimension must declare a low/mid/high anchor, matching score, evidence,
  and rationale under `recombinant-evaluation-guideline/1`;
- deterministic hard-gate rules produce `reject`, `defer`, `preserve`,
  `bounded_probe`, or `progress` without granting mission authority.

The ordinal score bands are explicitly marked `provisional_ordinal_anchors`.
They make reviewer usage reproducible but do not claim an empirically calibrated
optimum, and they do not drive disposition selection. Historical Palamedes cases
must still calibrate or replace the bands.

## Claims that should not be imported

- "Rarer is better."
- "There is a universal optimal novelty score."
- "Forward citations equal product, user, or moral value."
- "Local knowledge automatically makes distant ideas safe or executable."
- "Atypical combinations are necessarily interdisciplinary or genuinely new."
- "Observed inverted-U associations prove a causal mechanism."
