# Contributing to Palamedes

Palamedes is research beta. The planning kernel is heavily tested, but the
pre-planner surfaces around it are active hypotheses rather than settled
design. Contributions are welcome at both layers as long as the distinction
stays visible in the code and in the claims made about it.

## Before you start

Read [`STABILITY.md`](STABILITY.md) to see whether the surface you are touching
is `stable` or `experimental`, and [`CONTRACT_VERSIONING.md`](CONTRACT_VERSIONING.md)
for how the persisted contract version moves separately from the release
version. Changing a stable surface has a deprecation window; changing an
experimental one does not.

[`PALAMEDES_INQUIRY.md`](PALAMEDES_INQUIRY.md) records the open questions the
project is still arguing with itself about. It is not a roadmap, and a change
that resolves one of those tensions should say so explicitly rather than
quietly picking a side.

## Setup

Palamedes has no runtime dependencies. `pyproject.toml` declares
`requires-python = ">=3.9"`, and the oldest supported interpreter has to parse
every module, so develop against something that still catches 3.9 syntax
errors or rely on CI to catch them for you.

```bash
git clone https://github.com/LEE-Kyungjae/Palamedes.git
cd Palamedes
python3 -m pip install -e .
```

`ruff` is the only development tool, pinned in CI to the version in
`.github/workflows/ci.yml`.

## Checks

Run these before opening a pull request. CI runs the same four.

```bash
make check                                   # compile + tests, kernel and scaffolds
make schema-check                            # runtime plan shape matches schemas/plan.schema.json
ruff check .                                 # E9 + F: syntax and pyflakes defects
python -m compileall -q . -x '(\.git|__pycache__|external_repos)'
```

The lint configuration in `pyproject.toml` deliberately selects only `E9` and
`F`. This codebase predates any formatter, and turning on style rules now would
reflow thousands of lines and bury real findings in diff noise. Add rules when
you are prepared to fix what they surface.

CI also installs the wheel into a clean environment and imports every module
named in the `py-modules` manifest. That manifest is hand-maintained, so a
module can work in a source checkout and still be missing from an install.

## Pull requests

- **One claim per change.** A pull request should be describable as a single
  statement that could turn out to be wrong.
- **Say what would falsify it.** If a change is meant to improve mission
  quality, name the observation that would show it did not.
- **Tests pin behavior, not implementation.** A test that restates the code it
  covers passes while the code is broken. Prefer a test that fails if the
  contract regresses.
- **Do not widen an authority boundary silently.** Palamedes is `plan-only`:
  it proposes missions and never acquires delivery authority. Anything that
  changes what the system may do on its own needs to be called out in the
  description, not just in the diff.
- **Evidence claims must match evidence custody.** The ledger distinguishes
  what a model asserted from what the host observed, and same-provider judging
  from independent judging. Do not label a result with a stronger custody than
  it has.

## Commit messages

Short imperative subject describing the change, matching the existing history:

```
Package runtime modules missing from the distribution manifest
```

Add a body when the reason is not obvious from the subject, especially when the
change is driven by a measurement. Include the numbers.

## Reporting problems

Include the Palamedes version, the Python version, the command you ran, and the
relevant `.palamedes/` record IDs if the problem happened during a cycle. The
ledger under `.palamedes/` usually contains more diagnostic detail than the
terminal output, since the terminal only shows state changes and decisions.

Do not paste `.palamedes/` contents that include private product direction into
a public issue. Record IDs are usually enough to reproduce locally.
