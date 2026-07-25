# Improvement Cycle 303

## Topic

Put typed epistemic objects inside the shared revision envelope.

## Deficiency

A lifecycle adapter alone does not prevent payloads from becoming untyped
fields, while fully independent objects could still own separate revision and
provenance metadata. Both patterns weaken atomic cross-object purpose changes.

## Improvement

Added `validate_typed_epistemic_revision_envelope` and an experimental schema.

Signal, constitution, interpretation, mission candidate, tournament, and
mission contract are explicit typed entries with unique object IDs, versions,
fingerprints, schemas, validators, and payload references. All entries point to
one revision ID. The envelope alone owns revision metadata and provenance;
entries cannot create private lifecycle state or escape into another database
or untyped plan fields.

## Scope boundary

Cycle 303 defines the common typed envelope. Cycle 304 will specify the signal
payload as strictly observational state.

## Verification

- focused mission tests: 817 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

A purpose revision can atomically change several typed meanings while retaining
one conflict, restore, and provenance boundary.
