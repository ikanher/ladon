# Blind mathematical adjudication: feasibility r18

The reviewer received the frozen audit contract, operational inputs, and raw
attempt/capture/completion/replay/trust evidence. Corpus expected outcomes and
earlier adjudications were withheld while the proof attempts were classified.

- Cases 01 and 02: the negative propositions have complete replay and
  trust-accepted proofs. The positive attempts are rejected because replay
  observes `sorryAx`; those attempts establish no positive proof.
- Case 03: the positive proposition `False → True` has a complete,
  trust-accepted proof. The negative attempt is rejected because replay
  observes `sorryAx`.
- Case 04: the positive proposition `∀ n, ∃ k, k = n` has a complete,
  trust-accepted proof. The negative attempt is rejected because replay
  observes `sorryAx`.

Across all eight attempts, operational input, generated source digest, capture,
CLI expected-source-digest argument, completion reference, replay body/source
digest, trust decision and proof-established flag agree. Accepted terms have
complete replay and no disallowed axiom. No false proof acceptance was found.

The review used read-only artifact/hash checks and inspected the accepted replay
terms. It did not independently reconstruct the runtime or rerun the Lean
capture/completion commands. See the durable audit thread in
`.codex/state/pitfall-baselines/board.sqlite3` (posts 13–14 and 18).
