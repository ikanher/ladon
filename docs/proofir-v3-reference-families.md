# ProofIR v3 reference families

| Family | Fields | Permitted target |
| --- | --- | --- |
| Topology | `premiseRefs`, `conclusionRef` | local statement subjects in the derivation owner |
| Rule/context | `ruleRef`, `localContextRef` | declaration/local-context subjects |
| Checker evidence | `checkRunRef` | check-run subject in the same environment, local or resolved external artifact |
| Subject result | check result `subjectRef`, claim `statementRef`, observation `subjectRef` | typed subject descriptor |
| Support/attachment | source and candidate refs | source/surface/declaration subjects under the attachment policy |
| Artifact | `artifactRefs`, external `artifactRef` | content-addressed artifact with exact environment and target descriptor |

Only topology edges participate in derivation navigation, slices, cycle checks, or
satisfaction. Evidence and attachment links are resolved and displayed but never
silently promoted into premises.
