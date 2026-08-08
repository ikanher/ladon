## Context

`ladon proof-search evidence` exists, but the text renderer only understands declaration `rows`, DAG selector syntax is immature, and real-repository success criteria are not encoded.

## Goals / Non-Goals

**Goals:** ordinary human CLI grammar, text/JSON parity, read-only warm queries, documentation, installed-wheel tests, and fingerprinted evidence-quality calibration.

**Non-Goals:** a special LLM command, implicit index refresh, automatic Lean/replay/checker execution, or latency-only benchmarks.

## Decisions

1. Extend the existing ordinary `proof-search evidence` tree with explicit `theorem`, `artifact`, `route`, and `triage` selectors. No LLM-specific surface is added.
2. Render canonical result dictionaries through section-aware text renderers. JSON is serialized atomically under an output-byte cap.
3. Warm evidence queries open the project-local database read-only and refuse missing/stale state unless the caller explicitly requests the existing build operation.
4. Portable fixtures gate behavior. Quux and Matrix-Factorization calibration is opt-in, fingerprinted, read-only, and predicate-based.
5. Update the authoritative skill only after installed CLI examples pass.

## Risks / Trade-offs

- [Text output becomes verbose] → compact defaults with explicit detail bounds.
- [Real repositories drift] → record commit/worktree/config/artifact fingerprints.
- [Skill/docs become stale] → validate examples against the installed wheel.

## Migration Plan

Add parser aliases only where needed, stabilize the explicit grammar in tests, update docs and skill, then remove the temporary `dag:start` selector form.
