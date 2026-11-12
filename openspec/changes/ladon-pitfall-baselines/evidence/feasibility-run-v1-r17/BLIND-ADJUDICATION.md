# Blind mathematical adjudication: feasibility r17

The reviewer received only operational inputs and per-attempt source, capture, completion, replay, trust and axiom evidence. Corpus roles and expected outcomes were withheld.

All four cases have one accepted proof and one trust-rejected opposite-polarity attempt:

- Case 01: the negative existential is replayed and trust accepted; the positive attempt is rejected because its term depends on `sorryAx`.
- Case 02: the negative existential is replayed and trust accepted; the positive attempt is rejected because its term depends on `sorryAx`.
- Case 03: `False → True` is replayed and trust accepted; the negative attempt is rejected because its term depends on `sorryAx`.
- Case 04: `∀ n, ∃ k, k = n` is replayed and trust accepted; the negative attempt is rejected because its term depends on `sorryAx`.

For all eight attempts, source digest, expected-source-digest argument, capture identity, completion reference, replay term/source digests and trust decisions agree. Accepted proof axioms are within policy. Rejected attempts are not evidence of the opposite proposition. No false proof acceptance was found.

Limit: the review did not rerun Lean or independently reconstruct the runtime/capture environment. It adjudicates the recorded formal claims and evidence.
