# Lift and spuriousness feasibility inventory

## Current result: bounded Task 1.3 accepted

The [public source-owned lift checker](public-lift-check.md) now supplies the
complete-claim and pointwise mapping checks, fresh source/environment ownership,
canonical semantic comparison and distinct realization/incompatibility/unsupported
outcomes for the explicit Nat/rational profile. Its seven-case gate passed under
one shared 30-minute deadline, accepted in independent review #1292. Task 3.1
still owns refinement/report integration. Generic analytic lifting and prose
fidelity remain unestablished; the imported-JSON classifier remains conservative.

The [planning feasibility experiment](native-lift-feasibility.md) and the earlier
inventory below are retained as historical evidence of the missing boundaries.

## Historical source inventory

The bounded source inventory found no current Ladon path that can authorize either a checked realization of an abstract witness under all original constraints or a proof that a particular abstract witness is incompatible with those constraints. Therefore the 30-minute three-outcome gate was not started: its required positive and spurious counterparts do not exist in the current formal/evidence model. No capability was fabricated from status labels, reviewer strings, generic receipt shape, or an incomplete search.

The only current projection is `classify_lift_result` in `src/ladon/proof_contract_refinement.py`. It accepts a bounded `search-incomplete` attempt, preserves the exact abstract witness, returns `unsupported`, leaves `originalClaimRefuted` false, provides no spuriousness evidence, and keeps `checked-realization-or-incompatibility` open. Tests reject caller-supplied incompatibility labels.

`rational_witness.check_witness` can replay exact closed rational goals at scalar assignments. It does not construct function-space objects or encode the complete original constraints. Correspondence interpretation validates bounded quoted source spans and lowers supported syntax but does not certify prose intent. Existing Lean application-probe receipts bind to exact generated goals, not to an end-to-end original-space realization or incompatibility theorem. Generic envelope and receipt validation cannot fill that semantic gap.

Independent inventory #1074 was accepted by root in #1076. The audit included `proof_contract_refinement.py`, `rational_witness.py`, `correspondence_interpretation.py`, `proof_contract_probe_review.py`, receipt readers, ProofIR validation, and current refinement tests. No files were edited for this probe.

## Evidence required to reopen

Before implementing either positive outcome, Ladon needs a source/formal interpretation identity and a complete constraint set bound to the abstract witness, plus a checker receipt for either (a) a concrete realization satisfying every constraint or (b) a proof that the witness cannot satisfy a named original constraint. These must be exercised alongside the unsupported case under one shared 30-minute deadline. Until such counterparts exist, unsupported remains the only authorized lift projection.
