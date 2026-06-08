# Scenario: Boundary creep in a FedRAMP Moderate ATO

Two production-traffic components are outside the authorization boundary. Third-party Slack integration has implicit inheritance but isn't documented.

## Expected findings

- FR-BND-001 × 2 (analytics + slack)
- FR-INH-001 (slack inheritance not recorded)

## Why this matters

FedRAMP ConMon will flag this within a month. POAM these now.
