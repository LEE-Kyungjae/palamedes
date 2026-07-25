# Improvement Cycle 282

## Topic

Require two beneficiary interpretations and three competing missions.

## Deficiency

A single interpretation can turn purpose reasoning into summarization, while one
or two mission candidates allow an apparent choice without a meaningful
alternative space. Mere counts are also insufficient when candidates repeat the
same external condition or ignore one interpretation.

## Improvement

Added `validate_interpretation_mission_competition_case` and an experimental
schema.

The comparison case now requires at least two distinct, plausible beneficiary
interpretations. Each interpretation carries supporting evidence and a
disconfirming observation. At least three independently competing missions must
reference known interpretations, collectively cover all interpretations, and
state distinct changed external conditions and distinguishing theses.

The contract explicitly says that selection is required and that one summary is
not sufficient.

## Scope boundary

Cycle 282 creates genuine plurality inside the case. Cycle 283 will freeze the
constitution and authority envelope before the signal stream is exposed.

## Verification

- focused mission tests: 733 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot pass the comparison by paraphrasing one beneficiary story; it
must select among materially different, evidence-addressable missions.
