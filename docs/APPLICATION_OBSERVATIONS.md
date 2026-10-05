# Application premises and contexts

`ladon proof-search check candidate` and verified discovery now observe the
selected declaration's elaborated type and full parameter telescope, alongside
each remaining goal's actual ordered local context. These are application
observations. They do not identify every mathematically necessary assumption,
prove that a residual is unavoidable, or establish the requested goal while
residuals remain.

Current packaged helpers emit `ladon-lean-semantic-v4/check-candidate` or
`ladon-lean-semantic-v4/check-candidates`. Accepted results include
`applicationObservationVersion: 4`, the exact `semanticProtocol`,
`selectedDeclaration`, and `residualContexts`. Each context corresponds by
ordinal to one `residualPremises` expression and records its observed metavariable
identity. Local rows retain order, distinct identities, types, let values,
binder kinds and dependencies on earlier locals. Introduced goal binders remain
visible even when the caller supplied no local context. Display names may repeat;
use local identities and structural expressions to distinguish them.

`selectedDeclaration` contains the selected declaration's name, elaborated
`typeDisplay` / `typeStructural`, and its independent full `binders` inventory.
Binder kinds report Lean's explicit (`default`), implicit, strict-implicit and
instance-implicit categories. This inventory includes parameters already consumed
by the proposed application. It is distinct from the remaining goals' local
contexts. Parameter dependencies refer to earlier declaration parameters.

The default compact projection displays the application outcome and remaining
propositions/context before evidence receipts. Collections and long strings may
be clipped; inspect the omission ledger and exact environment/check references.
Use `--projection audit` for the full embedded observation, or the evidence
expansion commands described in [CLI.md](CLI.md). A context's `residualOrdinal`
preserves its association within a bounded projection. Missing rows in a clipped
view must not be interpreted as empty contexts.

V4 application identities use fingerprint scheme `lean-candidate-application`
version 2, binding the observation version, original single/batch protocol,
ordered structural contexts and declaration inventory with existing application
inputs. Stored reconstruction validates their canonical ownership. Mixed-version
batch frames, incomplete versioned observations and conflicting owners fail
validation. This identifies recorded evidence; it does not authenticate a live
session or turn a stored observation into a new check.

Historical v3 results retain their original identity and remain readable. They
lack the new context and declaration inventories; compact views disclose those
fields as unavailable rather than infer them from names, receipts or residual
text. The strict helper protocol changed explicitly; top-level public result
schema names remain unchanged for these additive fields.

Hand-written goal/context exploration and optional scratch checking retain their
existing behavior. This observation feature does not replay a completed
application against a captured source goal. A successful intermediate application
or an old accepted receipt is not new completion evidence. Source capture and
explicit completion have separate contracts.
