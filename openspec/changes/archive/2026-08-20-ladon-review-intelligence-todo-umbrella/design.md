## Context

Ladon now has a useful Lean review-routing core: module-DAG analysis,
architecture policies, generated/handwritten separation, duplicate import
reporting, facade subtype detection, configurable source-pattern scans,
declaration graph triage, optional ProofIR route audits, and atlas workflow
surfaces. Matrix-Factorization smoke runs showed that these seams catch the
known sampler-boundary problem when policy is supplied, but they also exposed
the next gaps: policies need to persist in repos, reports need stronger
prioritization, common-layer candidates need better ranking, generated pressure
needs attribution, and deeper Lean semantics should remain clearly separated
from parser-level hints.

The main constraint is generality. Ladon must not learn Matrix-Factorization
module names, sampler families, stale terms, bridge names, or project-specific
trust vocabulary. Target repositories must supply those policies; Ladon should
provide reusable policy contracts, ranking, evidence, and validation.

## Goals / Non-Goals

**Goals:**

- Turn the current TODO list into child-ready packets that can be implemented
  incrementally.
- Keep all project-specific names in repo policy files, policy packs, fixtures,
  or smoke inputs.
- Make policy-backed findings easier to act on by ranking pairs, files,
  contexts, common-layer candidates, facade quality, and generator evidence.
- Add benchmark/oracle coverage before promoting new finding classes.
- Define future Lean-backed semantic tracks for theorem-surface changelogs and
  proof x-ray without calling parser candidates proof dependencies.

**Non-Goals:**

- No hard-coded Matrix-Factorization, Quux, sampler, or stale-term knowledge.
- No full elaborated proof-dependency engine in this umbrella.
- No proof-correctness, theorem-truth, witness-adequacy, or artifact-authority
  claims by Ladon.
- No automatic source rewrite or import refactor as a first step.
- No graph database, web UI, LLM explanation layer, Rust rewrite, or broad
  product redesign in this umbrella.

## Decisions

1. Policy persistence comes before more project-specific checks.

   Repo-local `.ladon/` policy files make a project repeatable in CI and avoid
   temp CLI-only runs. The architecture and source-pattern policy seams already
   exist; the next step is validation, documentation, examples, and report
   visibility for which policies were discovered.

2. Fix-oriented triage is additive metadata, not a new authority model.

   Findings can carry suggested actions such as extract-common-layer,
   explicit-bridge, facade-cleanup, obsolete-import, or generator-cleanup, but
   the wording must stay as review guidance. Ladon can say "inspect this first"
   or "this looks like a common-layer candidate"; it must not say the design is
   wrong merely because a metric is high.

3. Common-layer and facade quality remain source-shape analyses.

   Common dependencies imported by multiple policy groups can indicate a lower
   layer, but high fan-in foundations may be intentional. Facade subtype
   classification should lower noise for pure public barrels and raise review
   pressure for mixed implementation/barrel files.

4. Generated attribution should point to cleanup ownership.

   Generated module tags and duplicate imports are most useful when grouped by
   likely generator family. The first implementation should report attribution
   and cleanup hints; it should not edit generated files or infer generator
   correctness.

5. Configurable lexical packs build on source-pattern policy.

   Reusable packs should remain data files or fixtures using the generic
   pattern engine. Built-in anchored Lean trust markers can stay as generic
   source facts, but stale terms and local trust words belong to policy.

6. Benchmark fixtures gate signal promotion.

   Every new review signal should have positive and negative fixtures, including
   false-positive boundaries. Matrix-Factorization smoke reports are useful
   development evidence, but portable tests should not depend on private sibling
   repos.

7. Lean semantic tracks are explicit future work.

   The theorem-surface changelog and proof x-ray tracks require Lean-backed
   extraction. They should label exact authority level: theorem type surface,
   parser candidate, elaborated dependency, tactic skeleton, axiom footprint,
   or quoted external status.

## Risks / Trade-offs

- Overfitting to Matrix-Factorization terminology -> Mitigation: keep all names
  in policies/fixtures and require generic tests with synthetic Lean modules.
- Report verbosity hides the top action -> Mitigation: summary-first text
  output with full detail in JSON.
- Fix suggestions sound like automatic refactors -> Mitigation: phrase as
  review actions and require source evidence for every suggestion.
- Common-layer ranking flags intentional foundations -> Mitigation: include
  confidence, scope, importing groups, and allow policy exclusions.
- Generated attribution guesses wrong owner -> Mitigation: make attribution
  heuristic and expose evidence; do not fail gates on attribution alone.
- Source-pattern packs become hidden hard-coding -> Mitigation: require explicit
  policy id/source and keep packs inspectable as data.
- Lean semantic changelog blurs proof authority -> Mitigation: label backend,
  confidence, source hashes/ranges, and nonclaims in every semantic row.
