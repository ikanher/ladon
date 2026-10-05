# r66 remaining-cost investigation and review boundary

Following r65 request preparation reuse, profiled the same selected real bundle
inspection using cProfile. Its stdout remains byte-identical to the r65 result.
No runtime code changed in this investigation. The bundle supplies 89 artifacts,
25 check runs and 14 distinct referenced environment artifacts.

The one instrumented execution takes approximately 17.94 seconds in the entrypoint;
profiling overhead makes that unsuitable for comparison with ordinary r65 timings.
Inclusive times overlap and must not be summed. `prepare_dossier` occurs once.
The evidence owner invokes `validate_envelope_batch` 26 times: once from catalog
resolution and 25 per-check execution/environment bindings. The profile attributes
10.10 inclusive seconds to stored checking-card validation and 7.39 to target
resolution. This identifies duplicated canonical-validation work across owners,
not proof that every repeated check is redundant or safe to omit.

Repeated context-manager generator calls include enter/exit and are not evidence
of duplicated dossier preparation. Distinct environment identities must not be
merged merely because their imported module inventories look similar. Any next
optimization needs an explicit owner-validated request-scoped contract preserving
malformed/ambiguous/mismatched context rejection, check receipt meaning and exact
outputs. No persistent cache or unchecked caller bypass was added.

The previous review froze further checking-core/interface investment pending
concrete needs. A lower request cost is an engineering contribution; whether a
batch receipt-validation route earns the scope/risk, or another existing workflow
should take priority, is unresolved. Current evidence does not identify another
unambiguous feature milestone. This is the decision for the r07 delta review.

Also reconciled stale live notes in the bundle, dossier and guide children. They
link the umbrella frontier instead of repeating old progress or instructing a
new reader comparison. Historical receipts retain their original candidates;
unmet provenance/profile/benefit gates remain open and deferred.
