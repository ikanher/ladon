## Why

The database can identify repository-wide evidence problems that are expensive and error-prone to discover by opening individual JSON artifacts. Ladon needs bounded triage queries that turn these gaps into prioritized review work.

## What Changes

- Add SQL-first triage for unattached/ambiguous surfaces, missing/stale/failed replay, conditional high-impact claims, stale checker witnesses, unsupported artifacts, and evidence disconnected from current declarations.
- Group findings by actionable reason, source owner, artifact, and theorem identity.
- Return deterministic bounded rows with coverage and authority context.
- Keep triage advisory and avoid converting ProofIR findings into Lean proof facts.

## Capabilities

### New Capabilities

- `ladon-proofir-repository-triage-queries`: Repository-wide ProofIR evidence health and review-priority queries.

### Modified Capabilities

## Impact

Affects stored SQL query services, result schemas, CLI selectors, indexes/query plans, and portable repository fixtures.
