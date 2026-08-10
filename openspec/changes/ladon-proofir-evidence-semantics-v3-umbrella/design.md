## Context

Ladon currently catalogs several ProofIR dialects and projects them into claims, surfaces, replay rows, DAGs, attachments, dossiers, and triage findings. The adapters preserve useful evidence boundaries, but compatibility conventions are becoming de facto semantics. Quux is a separated research playground and is outside Ladon's inspection, execution, dependency, and calibration boundary.

## Goals / Non-Goals

**Goals:** define one small native-v3 proof-evidence kernel; preserve exact authority and coverage boundaries; derive SQLite and review views; remove legacy ambiguity; close the expert-review blockers before semantic freeze; make Rust parity feasible.

**Non-Goals:** a universal proof-term AST, a new theorem prover, implicit Lean execution, direct Quux dependencies, in-place SQLite migration, or treating successful processes as theorem truth.

## Decisions

1. Fourteen changes form six operational waves: alpha identity/observation/attachment/schema; derivation and projection; first pre-freeze hardening; r03 blocker closure; freeze evidence; Rust parity.
2. Every child begins with red conformance fixtures or invariant tests before production edits.
3. Canonical artifacts remain immutable filesystem objects; SQLite remains a disposable projection.
4. The semantic kernel is envelope, environment, subject, claim, step, observation, and coverage. Surfaces, dossiers, cards, and governance witnesses are derived projections or namespaced extensions.
5. Quux is a separated research playground and SHALL NOT be inspected, executed, imported, or used for calibration. Ladon/ProofIR algorithms are independently implemented and proven with portable owned fixtures.
6. Child capability specs are copied byte-for-byte into the umbrella and governed by a machine-readable dependency ledger.
7. Rust work cannot begin until the six pre-freeze review children are green and v3 canonical bytes, schemas, validation diagnostics, normalized rows, query results, and packet provenance are frozen by the language-neutral corpus and review boundary.
8. Legacy ProofIR kinds are deleted rather than converted. Discovery emits one stable unsupported-legacy diagnostic and never projects their content.
9. The first implementation pass is an accepted alpha architecture, not a frozen semantic contract. Checked alpha tasks remain historical construction evidence; review-invalidated freeze and release claims are represented as stale until the hardening children pass.
10. Immutable typed payload models are the only validation authority. Envelope dispatch may select a model but SHALL NOT reimplement a weaker parallel validator.
11. Declaration identity, statement/type identity, optional value identity, and candidate-application identity are distinct typed subjects.
12. Incremental reference closure is evaluated over existing database artifacts union the incoming atomic batch. External checker references do not become derivation topology.
13. The Lean worker uses request-bound framed output and direct MetaM elaboration. It does not synthesize a `sorry` theorem or parse target-controlled stdout by searching for a brace.
14. The r03 review reopens any exit class contradicted by adversarial evidence even when its earlier implementation tasks remain historically checked.
15. Candidate-application identity commits to the environment, exact rule, conclusion, ordered substitutions, ordered residuals, and structured local context. Introduced Lean binders are evidence, not disposable elaborator state.
16. All artifact-reference families and fingerprint schemes use shared typed registries. Dependent query sections propagate parent truncation or independently query the complete selector population.
17. A database lock is owned by a nonce plus file identity; cleanup and stale recovery use compare-and-delete/claim semantics and never unlink a path merely because it has the expected name.
18. The freeze packet uses the strong manifest implementation itself. Unknown/old manifest shapes, empty inventories, unadvertised files, missing command records, and incomplete replay closure fail validation.

## Risks / Trade-offs

- [Deleting compatibility loses useful semantics] → rewrite only useful semantic cases as native-v3 fixtures, without retaining legacy field or serialization contracts.
- [A broad redesign stalls integration] → children have narrow ownership and executable exit gates.
- [Research algorithms leak into production dependencies] → CI runs portable gates with Quux absent.
- [Identity changes break stored references] → require a clean artifact regeneration and disposable database rebuild; do not migrate stale rows.
- [Parallel validators drift] → delete duplicate field checks and construct the immutable typed payload model exactly once.
- [A broad corpus becomes expensive] → use minimal pairwise fixtures per kind and reserve aggregate cases for bounds, cross-artifact closure, Unicode, rows, and query projections.
- [Worker framing is mistaken for proof authority] → frame transport integrity separately from Lean checker guarantees and subject results.
- [Introduced binders disappear from evidence] → serialize local declarations in dependency order and bind application/check identities to that context.
- [Bounded child queries overstate completeness] → expose `matchedAtLeast` and `truncationCause`, and never claim exact dependent counts after parent truncation.
- [A cleanup races a replacement lock] → retain an unpredictable owner token and compare current path identity before any unlink.
- [A packet verifier accepts an old manifest vacuously] → validate the manifest schema and exact archive inventory before iterating file rows.

## Migration Plan

Delete the obsolete compatibility packets and routes. Land the alpha native-v3 envelope, identity, observation, attachment, derivation, and SQLite surfaces. Retain those steps as history. Apply the r03 closure recipes to nested validation, local-context/application identity, reference/query semantics, worker isolation, lock ownership, and the actual packet builder. Build and clean-replay a content-addressed expert packet, then obtain a new blocker-by-blocker disposition. Start Rust only after that later packet closes the r03 blockers and cross-language fixture hashes, diagnostics, normalized rows, and query projections are immutable.

## Open Questions

- Which Lean environment inputs form the minimum sound Merkle manifest? This remains an explicit freeze decision in the typed-schema child rather than an implicit worker convention.
- Which initializer-free Lean environment-loading API is supportable across the pinned Lean toolchain? Until answered and tested, the worker exit class remains partial.
