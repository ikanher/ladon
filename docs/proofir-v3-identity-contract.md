# ProofIR v3 identity contract

| Identity | Exact scope | Primary use |
| --- | --- | --- |
| Declaration identity | environment + qualified declaration name + declaration-identity scheme/digest | exact attachment and checker rule reference |
| Statement/type identity | environment + expression-fingerprint scheme/digest | structural search and statement comparison |
| Value/proof identity | environment + qualified declaration + value-fingerprint scheme/digest | optional declaration-value observations |
| Candidate-application identity | environment + rule + conclusion + substitutions/residuals + application scheme/digest | checker observation of an application shape |
| Check-run identity | supervisor command/executable/helper/output/environment observation | process/checker provenance |

A type fingerprint may be equal for two declarations. It is never sufficient to
select a declaration attachment without the exact qualified name or emitted
declaration reference. A candidate application may be accepted while its
conclusion remains `unchecked` when residual premises exist.
