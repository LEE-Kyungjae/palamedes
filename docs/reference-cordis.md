# Cordis reference boundary

## Frozen references

- `cordiverse/cordis` at `8cc9e33fab69e2d0476d126baaf2acb24e6a6ab4`
- `cordiverse/paper` at `948a07b369c62adb3b12e102458be5c18dfb69b9`
- local paths: `/Users/ze/work/ref/cordis`, `/Users/ze/work/ref/cordis-paper`

The paper is an actively revised preprint and Cordis has an unstable API. Palamedes does not add
a runtime dependency on Cordis in cycle 402.

## Transferred mechanism

Cordis defines temporal composability as reverting a removed component's effects and spatial
composability as declaring and reactively managing component dependencies. Palamedes transfers
that mechanism only after mission selection:

- planning components declare `requires` and `provides`;
- every requirement must be supplied by another component or an explicit external dependency;
- effects are classified as `reversible`, `compensatable`, or `irreversible`;
- reversible effects require rollback, compensatable effects require compensation, and
  irreversible effects require a distinct approval gate;
- phases have entry and exit gates so a failed premise does not silently authorize later work.

This analogy is not an identity claim. Cordis manages software runtime context. Palamedes planning
may affect people, public communication, money, production data, and other states that cannot be
mathematically inverted.

## Product boundary

Cordis does not discover users, invent content, select value propositions, estimate resources, or
produce service concepts. The new planning brief must do that work before dependency and effect
lifecycle structure is useful. Mission selection remains separate from planning, and a planning
brief still grants no execution authority.
