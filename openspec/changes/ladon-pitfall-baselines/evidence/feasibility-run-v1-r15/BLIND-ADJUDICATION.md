# Blind review of feasibility run r15

Reviewer received only the operational inputs and per-case capture/completion/replay/trust reports. Corpus roles, expected outcomes and this conversation were withheld. A separate protocol auditor reviewed implementation/evidence custody without inspecting mathematical labels.

## Mathematical/evidence findings

- `assumption-feasibility-01`: the positive attempt was rejected because its proof depends on `sorryAx`; the replayed negative proposition is trust-accepted. The inconsistency outcome is justified by the accepted negative proof alone.
- `assumption-feasibility-02`: the positive attempt was rejected because its proof depends on `sorryAx`; the replayed negative proposition is trust-accepted. The inconsistency outcome is justified by the accepted negative proof alone.
- `assumption-feasibility-03`: the positive proposition is replayed and trust-accepted; the negative attempt is rejected for `sorryAx`. The witnessed outcome is justified by the accepted positive proof alone.
- `assumption-feasibility-04`: the positive proposition is replayed and trust-accepted; the negative attempt is rejected for `sorryAx`. The witnessed outcome is justified by the accepted positive proof alone.

No rejected attempt was treated as proof of the opposite proposition. The reviewer independently checked capture/source digest links, target types, completion/replay request identities, term/source digests, declaration types and axiom/trust records. There was no false proof acceptance in these four formal checks.

The original generated `Probe.lean` files were overwritten between polarities. The eight files in `reconstructed-probe-sources/` were regenerated from each case's recorded operational input and the frozen runner's source template; each SHA-256 matches its corresponding capture report. These are digest-verified reconstructions, not original retained files.

## Protocol review findings

The successful case outcomes do not qualify the family baseline. The worker starts its 600-second clock after host preparation and runtime setup; the launcher permits 720 seconds, then the host checks total time after return. Timeout or worker exceptions can leave no terminal case/index receipt. The policy and runner bytes are not bound in the index, tactics/bounds are hardcoded separately from policy, and capture/completion argv are not retained. Isolation results are strong for successful cases (26 exact import probes per case; both guard booleans true), but raw unrelated-failure and deliberate-exposure receipts are absent.

## Disposition

This is a blind mathematical adjudication of the recorded proof attempts, not acceptance of Task 1.4. Keep the index `pending-independent-adjudication` until Task 1.3 protocol defects are repaired and a fresh immutable batch is run. The r15 index and first case reports remain unchanged.
