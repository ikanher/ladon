## 1. Text Audit Surface

- [x] 1.1 Add typed audit-command and resource-directive IR with stable IDs and authority fields.
- [x] 1.2 Extract comment/string-safe `#check` and `#print axioms` rows with bounded subjects.
- [x] 1.3 Extract numeric `maxHeartbeats` and `maxRecDepth` values, meanings, ranges, and lexical scopes.
- [x] 1.4 Classify declaration-empty modules containing audit commands as command-only review roots.

## 2. Optional Lean Enrichment

- [x] 2.1 Reuse the existing helper to attach resolution and axiom-query results when available.
- [x] 2.2 Preserve lexical rows through unavailable, unresolved, partial, and timeout states.
- [x] 2.3 Thread containing owner, referenced owner, backend authority, population, and nonclaims into reports.

## 3. Acceptance

- [x] 3.1 Add positive fixtures for checks, axiom queries, finite/unlimited heartbeat, and recursion depth.
- [x] 3.2 Add negative fixtures for comments, strings, unsupported expressions, and ordinary theorem modules.
- [x] 3.3 Test deterministic IDs, bounded rendering, text/JSON parity, and partial Lean enrichment.
