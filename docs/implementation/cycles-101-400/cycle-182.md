# Improvement Cycle 182

## Topic

Treat revenue as sustainability evidence, not the sole mission selector.

## Deficiency

Revenue could either be ignored as morally suspect or promoted into the only
mission selector. The first choice hides resource reality; the second lets
payment redefine beneficiary value and override constitutional limits.

## Improvement

Added `validate_revenue_role_in_mission_selection` and an experimental schema.

Revenue has exactly two roles: sustainability constraint and market signal.
Mission comparison must also cover beneficiary change, constitutional fit, and
option value. Revenue cannot define beneficiary worth or override the
constitution, and a high-revenue ineligible mission cannot be selected.

## Scope boundary

Cycle 182 locates revenue within plural value. Cycle 183 will require every
mission to explain how resources renew or identify an explicit subsidy mandate.

## Verification

- focused mission tests: 333 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Revenue informs whether a mission can persist and whether demand exists, but it
never becomes the sole definition of what is worth pursuing.
