# Formal producer baseline and a concrete extension boundary

The current public formal producer successfully observed all three selected
original statements and extracted **zero contracts**. It preserved their typed
Lean observations and returned `unsupported-domain` at `telescope.b0.type`.
The recognizer only admits the natural-scalar estimate profile; a larger
binder allowance cannot supply the missing type and predicate meaning.

| Existing declaration | Source observation | Contract | Initial classification |
|---|---|---|---|
| `inverse_finiteJets` | observed, snapshot verified | none | Fixed loss five, unsupported domain |
| `nonbarPart_finiteJets` | observed, snapshot verified | none | Fixed loss four, different operator, unsupported domain |
| `applyMultiplier_finiteJets` | observed, snapshot verified | none | Symbolic loss, unsupported domain |

These operations took **38.36 seconds total** and peaked at approximately
**5.04 GiB**, under the unchanged 12 GiB cap. All command exits were successful;
unsupported semantic coverage was retained. The baseline is a producer capability
measurement on informed examples, not a classification or discovery benchmark.
See the three original JSON snapshots, their command receipts and
[verification](VERIFICATION.json).

[The proposal](PROPOSAL.md) defines the smallest concrete extension considered:
a separately versioned, typed real derivative-bound profile with admitted
predicate meaning, constant dependencies, sign guards and fixed literal loss.
Its first acceptance target is **2/2 fixed-loss source contracts** from the
current baseline **0/2**, while the symbolic-loss case remains unsupported.
New rules need their own checked Real-valued/predicate laws and source bindings;
they cannot inherit the current profile's Nat semantics by renaming it.

The proposal also corrects two tempting acceptance errors. A genuine new
four-loss inverse statement must retain its observed four-order requirement;
it cannot be rejected solely because the known theorem requests five. Changing
a frozen statement invalidates that evidence, while failure to apply the old
five-order theorem does not refute the altered proposition. Mean removal is a
valid different endpoint, so it must not be silently used as inversion.

The [independent scout review and root reconciliation](REVIEW.jsonl), posts
1541–1542, identify the profile and consumer impacts. Root retains the narrower
proposal: exact typed admission, fixed shifts, a uniformity distinction, and
honest unsupported behavior. Paper-norm equivalence, a sharper inverse theorem,
and unfamiliar-source detection stay outside that acceptance claim. No new
paper proof or generic analytic-norm framework is proposed.

Verification confirms all **2,670 original primary files**, all **51 previous
route-audit artifacts**, and the recorded relevant runtime files are unchanged.
The three formal snapshots pass the existing freshness/identity verifier.
No runtime/profile edits, new formal proof, test-suite rerun, commit or push
occurred. The existing statement and source-goal checks remain reusable for
their recorded scopes.

The current umbrella design explicitly freezes further runtime expansion.
Implementing this new mathematical profile therefore needs a scope decision;
this local proposal does not silently change that policy or complete task 2.1.
The umbrella remains **8/12**, with the same four acceptance gates open.
