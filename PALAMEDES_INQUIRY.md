# Palamedes Inquiry

Palamedes is not governed by a finished doctrine. This document preserves the
questions that currently shape the project so later implementation does not
silently replace inquiry with a cleaner retrospective story.

The detailed conversation record is
[`docs/inquiry/2026-07-25-origin-and-evolution.md`](docs/inquiry/2026-07-25-origin-and-evolution.md).

## Starting observation

The project began from an observation that probabilistic language models often
produce competent but convergent content. Common training distributions,
alignment, prompting, decoding, and evaluation can all reward familiar forms.
Palamedes initially explored whether references and explicit planning structure
could help people move beyond those familiar forms.

This premise is no longer treated as timeless fact. During development,
reasoning models, RAG, long context, tool use, inference-time search,
multi-agent debate, memory, repository indexing, and environment feedback all
improved. Some of the original problem may have moved or been partially solved.
Palamedes must compare itself against those systems rather than assume its
original necessity.

## Ideas currently in tension

These are not alternatives that must be resolved immediately:

- creativity and commercial success;
- divergence and decision closure;
- cumulative knowledge and discontinuous discovery;
- independent exploration and multi-agent criticism;
- general-purpose models and Palamedes-specific fine-tuning;
- reference collection and genuine internalization;
- preserving a fragile possibility and responding honestly to evidence;
- changing direction through learning and drifting toward whatever is newly
  interesting.

No item above is designated the winner. Palamedes should expose what each lens
reveals and what it hides.

## Working concepts

These definitions are hypotheses, not final ontology.

### Insight

An insight is a change in the perceived relation between observations that
alters what the past means and what questions or actions become possible next.
It is not merely a polished statement.

### Creativity

Creativity includes noticing anomalies, connecting distant lineages,
reframing a problem, generating possibilities, recognizing which fragile
possibilities deserve time, materializing them, and learning from contact with
reality. Novel output alone is insufficient.

### Originality

Originality may be relational rather than absolute. The same work can be an
obvious next layer to someone who knows its lineage and a shocking discontinuity
to someone who missed the intermediate layers. Personal novelty, contextual
novelty, and lineage-level novelty should not be collapsed.

### Development

Development is not only execution of a prior plan. Building exposes constraints
and observations that were unavailable before implementation. A project may
improve through repeated movement:

```text
view -> small step -> contact with reality -> changed view -> next step
```

This does not excuse arbitrary pivots. A claimed view change should preserve
the prior view, its trigger, the new evidence, newly opened paths, and possible
new blind spots.

## Current product hypothesis

One possible value of Palamedes is to preserve and interrogate the evolution of
viewpoint across people, models, references, implementation, and outcomes.
This is deliberately stated as a hypothesis rather than the new final identity
of the project.

The smallest product change justified by the inquiry is a structured
`view_transitions` lineage:

- previous view;
- trigger or encounter;
- new view;
- blind spots introduced by the new view;
- newly opened paths;
- next probe;
- source and related references.

## Reference-library hypothesis

`/Users/ze/work/ref` is more than a pool of code for retrieval. The history of
what was collected, revisited, adopted, rejected, and reused may reveal a
person's or project's unspoken research trajectory.

This must not be inferred from cloning alone. Weak and strong signals should be
distinguished:

```text
clone < revisit < cite < apply < retain after outcome < reuse across projects
```

Collection can also be noise, trend following, opposition research, or a
substitute for thinking. Palamedes should preserve why a reference mattered and
what later happened, not equate library size with understanding.

## Multi-model and fine-tuning hypothesis

Model competition may be useful when proposals are initially independent,
perspectives and evidence genuinely differ, criticism is bounded, judging is
blinded, and reality supplies the eventual result. More debate is not assumed
to be better; convergence, persuasion bias, judge bias, and compute inflation
must be measured.

Fine-tuning was raised as a counterfactual question, not as an intended
Palamedes roadmap item. Its purpose was to prevent the conversation from
assuming that the current system architecture was the only possible answer and
to widen the assistant's analysis. Palamedes is not currently planning to
fine-tune a model.

If this premise is ever reopened, it should require a new explicit decision and
verified operational data rather than being inferred from the earlier
discussion:

```text
context -> proposal -> criticism -> human choice -> action -> outcome
        -> correction and label -> possible training data
```

## Critical counterweights

Palamedes should actively test these failure possibilities:

- a beautiful genealogy may be a retrospective story rather than causation;
- shock may measure an observer's missing knowledge rather than originality;
- anti-generic optimization may reject a simple good answer;
- new perspective may become a justification for avoiding sustained work;
- repository accumulation may create noise and citation theater;
- creativity metrics may reward strangeness or performative insight;
- an expanding philosophy may prevent a concrete product from closing;
- Palamedes may amplify the creator's exploratory strengths and the creator's
  difficulty ending exploration at the same time.

## Immediate inquiry

Apply Palamedes to one live project for repeated development cycles. For each
cycle, preserve:

1. the current view;
2. the next small step;
3. what that step was expected to reveal;
4. what actually happened;
5. the resulting view transition;
6. what remained unchanged;
7. the next probe and why.

Compare this record with ordinary notes and a strong general-purpose LLM. The
first claim to test is not that Palamedes creates successful companies. It is
whether Palamedes preserves meaningful changes of view, reduces retrospective
distortion, and helps select steps that produce useful new information.

## Memory semantics

Conversation content must not be promoted silently into product intent.
Palamedes now distinguishes:

- `inquiry_items`: what kind of statement was made, why, and with what degree
  of commitment;
- `view_transitions`: how a frame changed and whether that change affects the
  plan;
- `reference_encounters`: how a collected reference actually influenced
  thought or implementation;
- `development_probes`: what a build step is intended to reveal;
- `open_questions`: tensions preserved without pretending indecision is a
  conclusion.

A question can widen reasoning without becoming a roadmap item. A changed view
can have `plan_effect: none`. Conversely, an explicit decision or commitment
must not be weakened into a merely interesting possibility.

## Revision rule

Do not rewrite this document to make the project look as though it always had
its current direction. Add dated inquiry records and explicit view transitions.
The path taken is part of the evidence.
