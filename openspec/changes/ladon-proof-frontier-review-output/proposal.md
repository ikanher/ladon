## Why

Proof discovery decisions disappear after an interactive session, leaving reviewers
to rediscover endpoints, consumers, unmatched fields, and rejected routes. Existing
packet evidence needs a declaration-level frontier without treating it as theorem
authority.

## What Changes

- Generate a source-linked frontier of compiled endpoints, immediate consumers,
  unmatched constructor fields, caller-supplied assumptions, and audit owners.
- Preserve accepted and rejected candidate routes with reasons, scope, index
  freshness, build status, and authority labels.
- Compare packet revisions using declaration type/source/dependency changes from the
  theorem-surface changelog rather than only file/module changes.
- Feed the compact frontier into existing packet-evidence reports without replaying
  or certifying the mathematical proof.
- Gate the six `TODO.md` acceptance scenarios as an integrated review handoff.

## Capabilities

### New Capabilities

- `ladon-proof-frontier-review-output`: Declaration-level proof frontiers, route
  history, revision comparison, and packet-evidence integration.

### Modified Capabilities

None.

## Impact

- Adds frontier schemas/renderers, packet normalization, revision joins, review
  artifacts, acceptance fixtures, and explicit proof-authority nonclaims.
