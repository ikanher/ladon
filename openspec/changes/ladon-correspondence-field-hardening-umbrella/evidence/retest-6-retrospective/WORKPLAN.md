# Proposed next implementation

Goal: preserve a discovered correspondence discrepancy through recording,
review, aggregation and reporting, independently of whether a false mathematical
statement has been established. This is a proposal, not completed runtime work.

1. **Retain findings in investigation output.** Add a source-bound finding
   projection for reviewed legacy claims and native reviews. Preserve statement
   relation, method relation, interpretation fidelity, formal support, proof
   dependencies, reviewer attribution and uncertainty separately. Review completed
   with a mismatch must still be visible after finish/finalize; it need not remain
   actionable forever. A false-assertion verdict requires its own evidence.
   Reuse existing judgments, source maps and response identities. Do not turn
   labels into machine-proved truth or reinterpret old receipts.
2. **Capture observations before expensive replay.** Add a lightweight public
   record/inspect operation, or extend an existing operation after consumer
   review, so a source-located candidate discrepancy can enter the queue without
   a successful ProofIR extraction. Bind a pending contract comparison and its
   evidence to the original passage. Promote the two retrospective cases through
   that path, retaining unresolved bridges. Require an explicit disposition for
   candidate observations; a separate valid proof or sufficient weaker theorem
   is not an automatic dismissal of correspondence mismatch.
3. **Integrate reporting and coverage.** Present mathematical falsity,
   correspondence findings, method differences and unexamined arguments as
   separate results. Distinguish survey completion from argument checks; permit
   an honest incomplete stop. Reconcile all observation IDs into the report even
   when bundles are stored in supplementary plans. Do not require every method
   difference to block completion. An observation-only plan may finish with
   findings and incomplete formal correspondence.

Primary owners: `investigation.py`, `investigation_correspondence_status.py`,
`investigation_correspondence_cli.py`, `investigation_cli.py`, and report/guide
consumers. Inspect existing formats before selecting a schema/version boundary.
`proofir_correspondence.py` and source maps already represent selected formal
links; extend them only if an actual consumer needs a new relation. The immediate
need is an explicit NL claim → selected formal guarantee → needed implication
→ attributed assessment relation, including an absent implication. A complete
automatic NL/Lean dual representation is unnecessary for this milestone.

The proof-dependency dimension should retain the B.11 containing-theorem fact
as a qualification. A later independent-reconstruction mode can constrain
dependencies if its consumer needs that guarantee. This work must not label a
valid endpoint theorem unsound merely because it cannot reconstruct its parent.

## Acceptance and evaluation

- Freeze the portable reporting proposal before production changes. Both
  mismatch/different cases currently lose their finding labels in v1 public
  status. Extend red cases to v3, aggregation, first-response preservation,
  contradictory reviews, absent counterpart, stale source and legacy readback.
- For the two reference cases, the final output must retain both located
  correspondence findings and “mathematical falsity not established,” without
  pretending native bridges were checked. Added hypotheses, changed domains or
  constants, and alternate proofs must remain explicit.
- For all six historical controls, retain recorded local support and scope.
  Report the two different methods without declaring their propositions false.
  Preserve B.11's proof-origin qualification and the lattice geometric-parent
  boundary. Do not silently replay or relabel the first responses.
- Verify no survey-only or extraction-failed case is reported as whole-paper
  certification. Review-completion, finding severity and mathematical support
  must stay separate. Candidate observations are authored, not automatically
  exhaustive inventories.
- Execute one ordinary-user workflow through capture, review and final output,
  with independent integration review and relevant focused/parent tests. No
  full mathematical rebuild is needed to test a report projection.
- Stop after that evidence and reassess. A new blind run needs a separately
  frozen, hint-free objective covering both mathematical errors and correspondence
  discrepancies, new run storage and pinned local runtime. Do not disclose the
  two locations or change the reference rubric after seeing results. These known
  cases are development controls; they cannot demonstrate unseen discovery.

If this work only improves reporting, say so. Measuring discovery benefit still
requires separately withheld material and a matched comparison. Extraction
scaling, content-addressed bundle storage and general claim-inventory automation
should wait for a demonstrated remaining bottleneck, rather than being bundled
into this correction by default.
