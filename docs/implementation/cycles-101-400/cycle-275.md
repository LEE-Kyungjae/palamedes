# Improvement Cycle 275

## Topic

Search metric-compliant missions for displaced cost and unobserved parties.

## Deficiency

A mission candidate can satisfy its declared metric while moving cost into
another workflow, later time, or less visible population. Metric language then
becomes a way to make harm formally out of scope.

## Improvement

Added `validate_hidden_harm_adversarial_criticism` and an experimental schema.

Even a metric-compliant candidate must undergo exactly two independent
searches: displaced cost and unobserved party. Each records an adversarial
hypothesis, method, searched scope, and evidence. A found harm names the
affected party or system, cost, status, and response. Any unresolved harm forces
revision or rejection; resolved harm requires mitigation evidence before the
candidate can regain eligibility.

## Scope boundary

Cycle 275 protects candidate evaluation from metric gaming. Cycle 276 will
protect the constitution itself from malicious amendment.

## Verification

- focused mission tests: 705 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot accept apparent metric success until an adversarial critic has
searched outside the metric's visible boundary for who or what paid the cost.
