## Context

The preceding packets establish private stored contracts. The final packet must
expose them through ordinary installed Ladon commands and prove that configured
artifacts are rebuilt with the index. Real calibration must measure answer
quality because current JSON lookup is already tens of milliseconds.

## Goals / Non-Goals

**Goals:**

- Provide ordinary text/JSON inspection for catalog, theorem evidence, artifact
  evidence, and obligation routes.
- Integrate configured artifact inputs into build/status/freshness behavior.
- Verify complete cross-evidence answers and bounded operational behavior.
- Update maintained docs and skill instructions.

**Non-Goals:**

- No LLM-only command, RPC, daemon, or editor protocol.
- No claim that SQLite is faster than `rg` for tiny artifacts.
- No automatic import of every file under `artifacts/generated` without config.
- No live Quux checkout dependency in portable tests.

## Decisions

1. Extend the existing ordinary `ladon index`/`ladon theorem` command families
   rather than adding a separate executable. Exact spelling follows existing
   parser conventions and must be documented before implementation tests are
   finalized.
2. Emit versioned render-neutral result dictionaries first, then text and JSON
   renderers. Results include generation, freshness, coverage, authority,
   truncation, diagnostics, and source links.
3. Build/status report ProofIR input counts and semantic coverage separately.
   Query commands default to warm DB reads and never rerun external checkers or
   Lean builds implicitly.
4. Portable fixtures own correctness. Quux and Matrix-Factorization harnesses
   are opt-in observations with repository fingerprints, commands, timings,
   and expected qualitative predicates.
5. The go/no-go quality gate requires one query to join a surface, bundle,
   replay provenance, declaration source, and lineage availability; and another
   to preserve conditional transitions through a CDC DAG route.

## Risks / Trade-offs

- [CLI exposes private SQL] → Keep table names out of public results and route
  all access through versioned query services.
- [Queries trigger expensive refresh] → Require explicit refresh policy and put
  progress on stderr; warm queries stay read-only.
- [Live calibration becomes brittle] → Record observations separately and use
  frozen excerpts for gates.
- [Documentation overclaims proof authority] → Reuse bridge trust language and
  include explicit negative CDC examples.

## Migration Plan

1. Add installed-CLI failing tests over completed storage services.
2. Add parser/orchestration and renderers.
3. Add two-build integration and wheel tests.
4. Update README, CLI/architecture docs, and authoritative skill.
5. Run portable suite, then optional fingerprinted real calibration.

## Open Questions

- Choose final subcommand names during the first task by inspecting current
  command grammar; tests and docs must use one stable spelling thereafter.
