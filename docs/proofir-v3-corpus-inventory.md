# ProofIR v3 conformance corpus inventory

This inventory is the freeze checklist for the native-v3 corpus. It intentionally
contains no legacy conversion cases beyond explicit rejection.

| Family | Registered kinds / seam | Required cases |
| --- | --- | --- |
| Envelope | all nine `proofir.*` kinds | valid, unknown kind, legacy kind, missing key, extra key, wrong version, detached-ID mutation |
| Nested schemas | environment, claim, derivation, plan, attempt-log, check-run, source-map, attachment-set, governance-observation | wrong scalar/container type, missing/extra key, enum, identifier grammar |
| References | local, external artifact, subject, premise, conclusion, checker, support, attachment | valid closure, dangling target, wrong target kind, environment mismatch, duplicate local ID |
| Derivation | ordered AND premises, OR alternatives, recursion/SCC metadata | repeated premise, cycle policy, complete step, residual/attempt distinction |
| Evidence | observations, authority, guarantees, coverage, omissions, limitations | accepted/unchecked distinction, partial/unavailable coverage, omission attribution, bound |
| Projection | every normalized SQLite row family | valid insertion, foreign-key rejection, atomic rollback, duplicate identity, indexed lookup |
| Queries | navigation, complete slice, satisfaction, alternatives, SCC, dossier | positive limits, exact/bounded counts, truncation, complete step fields, no N+1 growth |
| Canonical profile | strings, controls, combining forms, non-BMP, invalid scalar, integers, floats, depth, collections | exact bytes/ID or stable stage/code/pointer/message |
| Resource bounds | artifact, batch, artifact count, database, query/output | below boundary, exact boundary, above boundary, prior-destination preservation |

The registered kind set is:

```text
proofir.environment
proofir.claim
proofir.derivation
proofir.plan
proofir.attempt-log
proofir.check-run
proofir.source-map
proofir.attachment-set
proofir.governance-observation
```

The supported environment manifest fields are exactly:

```text
prover: {name, version}
toolchain: {name, version, commit}
dependencies: [{name, version, source, digest}]
compiledModules: [{module, digest}]
options: non-empty string-keyed scalar map
trust: {axiomsAllowed: string[], unsafeAllowed: bool}
fingerprintScheme: {name, version}
```

The corpus remains a language-neutral contract. Rust is not admissible until the
executable corpus covers every row above and the semantic-freeze review packet
records a clean extracted replay.
