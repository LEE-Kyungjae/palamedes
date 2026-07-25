# Improvement Cycle 184

## Topic

Separate durable benefit from exploitative growth mechanisms.

## Deficiency

Growth could be interpreted as beneficiary value even when it resulted from
switching friction, compulsion, or purchased distribution rather than voluntary
durable benefit.

## Improvement

Added `validate_growth_mechanism_audit` and an experimental schema.

Every growth observation separately assesses voluntary durable benefit,
switching friction, compulsion, and acquired distribution using evidence and a
discriminator. Growth is never direct proof of value. Durable-benefit
classification requires present voluntary benefit and no known friction or
compulsion; exploitative mechanisms block scaling.

## Scope boundary

Cycle 184 interprets growth quality. Cycle 185 will make new missions consume a
finite exploration budget and identify the option they displace.

## Verification

- focused mission tests: 341 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Growth supports a mission only after its mechanism is separated from friction,
compulsion, and acquired distribution.
