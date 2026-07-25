# Elaboration-Surface Benchmark Handoff

## Portable fixture

The downstream `ladon-signal-benchmark-harness` can adopt the tracked Lake
project at `tests/fixtures/lean_declarations`. Its `lean-toolchain` pins Lean
4.32.1, and the required acceptance command is:

```text
uv run --locked python scripts/lean_declaration_gate.py --required
```

The fixture supplies these independently checkable cases:

| Case | Declaration | Required signal |
| --- | --- | --- |
| declaration kinds | `theoremKind`, `definitionKind`, `axiomKind`, `opaqueKind`, `unsafeKind` | real kind, source range/hash, and unsafe status |
| structured statement | `structuredStatement` | implicit, instance-implicit, and explicit binders; premise `True`; conclusion `True` |
| imported notation | `importedNotation` | rendered elaborated type plus printer and Lean version |
| parser disagreement | `parserElaboratorDisagreement` | `lexicalGhost` remains parser-only while `Nat.zero` and `Nat.succ` are value dependencies |
| imported target | `rootUsesImportedDependency` | named imported stub in root scope and full-row replacement in inventory scope |
| direct trust | `directSorry`, `directAxiomReference`, `axiomKind` | scoped direct `sorryAx`, axiom-reference, and declared-axiom facts |
| body bound | `largeProofBody` | statement remains readable and full source body is omitted with explicit truncation |

Frontend-generated macro constants are deliberately absent from the normalized
review inventory when a parser declaration inventory is available. The parser
inventory is only a declaration whitelist in that operation; parser candidates
remain parser-authority evidence and are never promoted to Lean dependencies.

## Conservative cap evidence

The implemented caps are 32 binders, 32 premises, 64 dependencies per
authority kind, 1,024 statement-source bytes, and 4,096 rendered-type bytes.
On the pinned fixture the observed maxima are 4 binders, 1 premise, 55 direct
constants in one dependency collection, and 62 rendered-type bytes. The large
proof occupies 1,304 source bytes while its retained statement excerpt is 30
bytes. Thus the fixture exercises body truncation and approaches the dependency
cap without truncating ordinary declaration structure.

On 2026-07-25, the deterministic raw elaboration payload contained 15 Lean
environment constants and occupied 30,264 canonical JSON bytes, below the
required 256,000-byte ceiling. Parser-inventory normalization retained 13
source declarations and added 18 named imported stubs. The complete normalized
report occupied 642,567 canonical JSON bytes and is guarded by a conservative
1,000,000-byte real-pipeline ceiling. These figures are reference observations,
not thresholds that future toolchains must reproduce byte-for-byte.

## Harness adoption

The downstream harness should record:

- the pinned toolchain and helper payload versions;
- pass/fail predicates for every row in the table above;
- canonical payload size and every collection's `total`/`truncated` pair;
- separate parser-candidate, type-dependency, and value-dependency edge counts;
- complete, partial, or unavailable status rather than treating missing
  elaboration as an empty observation.

Cap tuning should require a broader corpus and may change only with explicit
schema/version evidence. These surfaces are navigation and direct Lean artifact
evidence; the benchmark must not reinterpret them as proof-correctness,
theorem-truth, or transitive axiom-closure results.
