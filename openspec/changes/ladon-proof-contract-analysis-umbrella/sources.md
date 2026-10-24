# Planning sources and reuse boundaries

Inspected locally on 2026-10-18. No online research was used. These are source observations for planning, not freshly executed theorem/build results. The hashes identify the inspected files; they are not a frozen evaluation runtime. Implementation must freeze the full dirty checkout separately before edits.

## 1. Ordered propagation

[Propagation.lean](/home/codex/projects/quux/Quux/Semantics/Propagation.lean)

Generic predecessor fold; Boolean, counting, min-plus and max-plus instances. Does not supply proof-hypergraph AND semantics or arbitrary mathematical transfer laws.

SHA-256: `f40584781be5fecd875a018dbb0bfdd61e3e1a7c05e732120e2e790948dfff21`.

## 2. Monotone fixed points

[OrderBellman.lean](/home/codex/projects/quux/Quux/Semantics/OrderBellman.lean)

Proposition-valued finite-state Bellman family. Motivates order discipline; cyclic contract propagation is deferred.

SHA-256: `3d559aee29ca6210c8e4e356adcf772b75650d8d608de6b8b423ea3236ead2f6`.

## 3. Antichain consumer

[AntichainFixedPointConsumerMini.lean](/home/codex/projects/quux/Quux/Problems/AntichainFixedPointConsumerMini.lean)

Exact finite diamond example reconstructing a down-set from an antichain. General mathematical-contract dominance and pruning still need justification.

SHA-256: `5be25de809a0f97c2fb85d1ea61111b3e17117c7cecdea1d34757a9041087765`.

## 4. Probe separation

[ProbeSeparation.lean](/home/codex/projects/quux/Quux/Semantics/ProbeSeparation.lean)

Separating-family interface and a symmetric rational matrix example. Not a general basis of probes for arbitrary theorem equivalence.

SHA-256: `4102aae20b1a8047eebb4050db26adc2621050578f37f4bcb3a5c53bf24795f0`.

## 5. Counterexample loop

[run_counterexample_guided_discovery_loop.py](/home/codex/projects/quux/scripts/run_counterexample_guided_discovery_loop.py)

Bounded dispatch and declared-reduction minimization pattern. Reuse the design; implement a Ladon-owned consumer with exact scope.

SHA-256: `8a722aa7eb273de46dc7de481f57a55bcdb353cd3d53181254890c548fad6748`.

## 6. Counterexample loop contract

[counterexample-guided-discovery-loop.json](/home/codex/projects/quux/docs/counterexample-guided-discovery-loop.json)

Finite survival, scoped minimality and explicit nonclaims. Supports the refinement authority boundary.

SHA-256: `2990992668552d01fd0e78749fe98274127225e33f6dfc39203366d610212e0d`.

## 7. Subset/subtype experiment

[PROOF-IR-SUBSET-SUBTYPE-TRANSPORT.md](/home/codex/projects/quux/docs/PROOF-IR-SUBSET-SUBTYPE-TRANSPORT.md)

Checked transport with curated mappings; dependent-domain semantic extraction explicitly remains partial.

SHA-256: `a9709625bab87ad3ab40065fb1529d7104dcaf13f2f521c541c2dc9920cdc033`.

## 8. ProofIR design notes

[proof-ir-ideas.md](/home/codex/projects/quux/paper/proof-ir/proof-ir-ideas.md)

Layered proof/discourse/obligation representations and explicit lowering certificates. Design inspiration, not shipped Ladon capability.

SHA-256: `cc28dbc05e86da1eac2d31a9c2a3968bee7cbc1de17d946c2e324c502c101d99`.

## 9. Existing structural solver

[_proofir_derivation_solver.py](/home/codex/projects/ladon/src/ladon/_proofir_derivation_solver.py)

Memoized bounded AND/OR support; budget-dependent unknown is not cached. Preserve current semantics and add a distinct mathematical evaluator.

SHA-256: `e3ad43c10ea75842b2420dfd0bbe87fe670a21aeca852b652eba1fa05c08e190`.

## 10. Existing interpretation lowering

[correspondence_interpretation.py](/home/codex/projects/ladon/src/ladon/correspondence_interpretation.py)

Scoped attributed source interpretations; supported fragment and opaque residuals. Reuse instead of a new prose format.

SHA-256: `db9468c2aa288c9c392924a3826d6439cb4efb39edce8a6d0b054d8bccd7c617`.

## 11. Existing native correspondence

[proofir_correspondence.py](/home/codex/projects/ladon/src/ladon/proofir_correspondence.py)

Source-bound interpretation/correspondence artifacts under native v3; structural validation does not certify prose fidelity.

SHA-256: `72747181cc11d108a4fcd13eaab23d2192e5ba535c2cd20ca18d2069dbceaf3d`.

## 12. Existing derivation challenges

[investigation_derivation.py](/home/codex/projects/ladon/src/ladon/investigation_derivation.py)

Source-bound authored steps and challenge context binding; reuse immutable identities and review boundaries.

SHA-256: `86bc2eab2b3d3bfa97f776d07af87cdf00d7c3e85fc3c9fef1f5e8ab6ad15ddf`.

## 13. Existing rational checker

[rational_witness.py](/home/codex/projects/ladon/src/ladon/rational_witness.py)

Safe exact premise/conclusion witness checking; reuse for finite rational probes and refinement.

SHA-256: `1fd4483488e538732c71884c056c20405f3d874f54f957be4ceebfe386e5c6ac`.

## 14. Existing findings

[investigation_findings.py](/home/codex/projects/ladon/src/ladon/investigation_findings.py)

Retains reviewed observations and correspondence discrepancies; new analysis must reach this report surface.

SHA-256: `85c8070ec6cda4baec02775efbda78df2bbdda7e946ed43c9ffab636578f5052`.

## 15. Existing goal completion

[source_goal_completion.py](/home/codex/projects/ladon/src/ladon/source_goal_completion.py)

Exact-context proof checking and replay; reuse for generated bridges and application probes.

SHA-256: `af0fbad0ae95430d039be2e73d2631cb1f324861921238758a99f5462b163c4b`.

## Existing specification boundary

The main native-v3 schema, exact identity, authority/coverage and derivation-hypergraph specs remain in force. New capabilities add mathematical contracts and consumers; they do not alter AND/OR meaning, treat opaque Lean fingerprints as semantic equality, or make Quux a runtime dependency. Child acceptance must demonstrate the new behavior rather than cite these examples as if they already implemented it.

## Evaluation custody

This planning packet is development material, not an auditor handoff. Fresh held-out evaluation inputs must be exported independently, without diagnosis, reference answers, selected fault locations or these development interpretations. Previous experiments and the existing retest-7 packet are preserved.
