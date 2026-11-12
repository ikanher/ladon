# Blind mathematical adjudication: feasibility r19

The reviewer examined operational inputs and raw capture, completion, replay,
trust and axiom evidence without expected labels or prior adjudications.

- Cases 01 and 02: the negative propositions have complete replay and
  trust-accepted proofs. Their positive attempts are trust-rejected because
  replay observes `sorryAx`.
- Case 03: `False → True` has a complete, trust-accepted proof. Its negative
  attempt is trust-rejected because replay observes `sorryAx`.
- Case 04: `∀ n, ∃ k, k = n` has a complete, trust-accepted proof. Its negative
  attempt is trust-rejected because replay observes `sorryAx`.

For all eight attempts, generated source, capture, completion, replay and trust
bindings agree. Accepted terms use only allowed axioms. The four rejected terms
are not proof evidence even though completion returned exit code 0.

The reviewer independently checked recorded evidence and did not reconstruct
the preserved runtime or rerun Lean. Peer-reviewed findings are in
`.codex/state/pitfall-baselines/board.sqlite3` (posts 22, 25 and 26).
