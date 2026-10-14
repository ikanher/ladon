# Fresh constructed-case comparison

The adjudicated first responses show **no detection or cost benefit** from Ladon
in this pilot. Both arms localized three justified faulty inferences and
correctly assessed all four controls, with no false alarms, false-endpoint
claims, or budget overruns. The remaining reference fault has a defensible
alternative source reading; neither arm receives unqualified fault credit for
it. Assistance took substantially more observed wall time.

This qualifies the implemented evidence path, not autonomous detection of the
historical exposition issue. The cases are short, constructed passages with
portable actual Lean proofs. They are separate from development fixtures and
historical target-paper audits; they are not held-out analytic paper passages.
No further full-paper run was started.

## Frozen protocol and first reports

[Protocol](pilot/PROTOCOL.md), [tooling](pilot/TOOLING.md),
[order](pilot/ORDER.json), and [scoring harness](pilot/score.py) were frozen
before primary dispatch. Eight independently curated inputs had nominal key
balance four faulty arguments, two faithful controls, one alternative-method
control, and one explicitly ambiguous control. At least two included valid
surrounding reasoning and an independently supported endpoint, without telling
auditors which inference to select. All eight actual Lean sources compiled
under the installed pinned Lean 4.32.1 before dispatch; the final compilation
receipts are [preserved](pilot/compilation-receipts.json).

There were exactly 18 fresh Luna-medium pilot contexts: curator, independent
source reviewer, and one fresh context per case/arm. Both arms received identical
public source bytes and compiled artifacts, the same model/configuration,
15-minute inclusive budget, and identical reviewer comments and allocated
reviewer cost. Ordinary auditors used local source/Lean tools. Assisted auditors
could additionally invoke the current Ladon source checkout. Each first response
was frozen within its 10-minute first-phase deadline before receiving comments.
All 16 corrections were separately saved within the original inclusive budget
and **before** key reveal. The [all-first barrier](pilot/ALL-FIRST-FROZEN.json)
precedes root/reviewer access to the key.

The shared filesystem provided procedural separation, not enforced isolation.
Inputs explicitly prohibited keys, other-arm answers, historical sources, online
searches, model APIs, packages and shared builds. No answer exposure was reported.
One auditor queried the global participant table outside its own thread limit;
this breach remains disclosed and prevents an enforced-isolation claim.

## Source adjudication and normalization

The [original reference key](pilot/original-reference-key.json) remains unchanged.
The reviewer independently examined original sources before primary responses,
then reviewed the key and frozen rows after unblinding. Its
[source/key assessment](pilot/key-adjudication.json) and
[row assessment](pilot/row-adjudication.json) qualify the references rather than
force disagreements into the key labels. Root dispositions are in
[ADJUDICATION.json](pilot/ADJUDICATION.json).

| Case | Selected source inference / control | Assisted raw first | Ordinary raw first | Adjudicated disposition |
| --- | --- | --- | --- | --- |
| `85f7f1c843c4` | Local/retained record implies catalog code | argument-fault | method-difference | Both identify the absent bridge. Ordinary first interpretation already says those facts do not imply the code; its label is corrected for inference scoring, with attributed evidence only. |
| `fe3d1c600ea6` | Even/divisible by two implies positive | argument-fault | argument-fault | Both checked the zero counterexample and separated the independent lower bound. This is conditional on the natural inferential reading of “then says.” |
| `c4d5434284cb` | Tea and tea-or-coffee imply coffee | argument-fault | argument-fault | Both checked countermodels and separated the independent survey record. |
| `b07c1d37ee10` | Bound followed by equality assertion | ambiguous | faithful | “Next asserts” need not mean equality follows from the bound. Calibration independently warrants equality; both first reports distinguish it from the invalid bound-only implication. No forced fault credit or interpretation-error penalty. |
| `df83178b3496` | Natural-number order transitivity | faithful | faithful | Valid control; actual formal application agrees with the described chaining. |
| `4549693104b8` | Modus ponens | faithful | faithful | Valid control; the stated premises imply the conclusion. |
| `7efc5c13032b` | Integer equality with two offered methods | faithful | faithful | Both are qualified correct controls. Normalize to the reference alternative-method control for inference accuracy only; exact procedure identity remains attributed. |
| `d4fbe7ff5619` | Undefined “usually” / “should” bridge | ambiguous | ambiguous | Correct ambiguity control. A compiled conditional with an added rule does not establish source-level endpoint truth. |

Counting only raw labels would give a mechanical 3-versus-2 fault advantage.
That would discard an ordinary auditor's correctly localized missing implication
because of its label. The predeclared protocol scores source localization and
valid evidence and requires adjudication of key disagreements. The independent
reviewer recommends the normalization above, yielding a tie. Both the
[raw-label rows](pilot/raw-label-first.json) and
[raw-label aggregate](pilot/RAW-LABEL-SCORE.json) remain available; they are not
the benefit decision. The method-control normalization treats both arms equally
and does not certify either exact method correspondence or an exclusive
prose/formal mismatch.

The calibration case and procedure control weaken the nominal reference
population: the former is not an unambiguous fault, and the latter is compatible
with one of the prose's explicitly offered methods. Those limitations are
reported rather than repaired with easier replacement cases. Evenness/positivity
also retains its sequencing qualification. This population cannot support a
general accuracy or historical-paper detection claim.

## Actual evidence and remaining formal links

Root replayed 36 original check files or exact recorded obligation terms:
28 accepted and eight expected rejections, all matching the first evidence.
All 41 frozen input identities remained unchanged. The
[replay receipts](pilot/root-replay-receipts.json) and
[summary](pilot/root-replay-summary.json) distinguish post-key validation from
first-response authority. Ordinary record-code reasoning remains attributed;
ordinary calibration performed no Lean check. Replaying later cannot grant
either report retroactive first-response kernel credit.

Three assisted auditors attempted the full interpretation/alignment/check path.
Modus ponens retained its supported conditional but four supplied correspondence
terms failed because they omitted or misused generated binders. The positivity
case retained conditional/provider support while two supplied transfer terms
failed. Transitivity retained conditional support, while Unicode-subscript local
names produced explicit unsupported-name and missing-transfer residuals. All
three parent correspondences remained unresolved; no failed tactic was scored
as a refutation. Other assisted findings used actual application slices plus
direct Lean checks or source reasoning; one opaque interpretation was retained
without claimed complete alignment.

All eight selected applications were independently re-extracted through the
final public CLI in private roots, matching their exact terms, ordered arguments
and local contexts. The coordinator initially omitted the scoped flag on one
replay; its mismatching profile result was preserved, then the original scoped
profile was replayed. This is a post-key qualification correction, not a new
primary run or an improved first result. Detailed receipts remain in
`.codex/state/nl-lean-e/root-replay/fresh-slices/`.

## Counts, time and cost

The frozen harness mechanically aggregates exactly
[16 normalized first rows](pilot/normalized-first.json) into
[SCORE.json](pilot/SCORE.json). Root checked the rows and totals.

| First-response measure | Assisted | Ordinary |
| --- | ---: | ---: |
| Cases retained | 8 | 8 |
| Justified selected faults | 3 | 3 |
| Correct controls | 4 | 4 |
| False alarms / false-endpoint claims | 0 / 0 | 0 / 0 |
| Interpretation errors / budget overruns | 0 / 0 | 0 / 0 |
| Explicit unresolved verdicts | 0 | 0 |
| Reported commands | 46 | 13 |
| Allocated observed first-response wall seconds | 2086.97 | 716.12 |

The assisted arm had two raw ambiguous responses; the ordinary arm had one.
The harness's explicit unresolved-verdict count is not a claim that all source
meanings or formal links were resolved. The calibration reference uncertainty
and incomplete correspondence links remain visible separately.

Elapsed wall time runs from root dispatch to durable worker completion; it
includes dispatch latency and excludes later root capture delay. Each arm pays
the identical 7.65175-second reviewer share per case. Including correction
completion and that share gives 2537.79 seconds assisted versus 1168.67 ordinary.
Every first/correction finished within its original deadline.

Tool-time sums in the harness are incomplete reported wrapper/receipt times
(351.23 versus 4.01 seconds), with some approximations and missing measurements.
They are not fully coordinator-observed tool cost, and commands are recorded
counts rather than complete process/API counts. Internal slice receipts retain
output sizes/digests without every temporary stream. Token usage, money,
coordinator active time and several setup costs were unavailable and are not
invented. [COSTS.json](pilot/COSTS.json) separately records curator/setup,
compilation, common review and post-key adjudication/replay costs. Cost benefit
uses observed allocated wall time conditional on comparable findings; assistance
did not reduce it.

Separate corrections changed ordinary record-code to argument-fault, assisted
calibration to argument-fault, and assisted procedure-control to ambiguous.
They are preserved in the paired snapshot directories and do not improve first
scores. The source review calling corrections “post-key” was inaccurate: the
board timestamps establish they preceded key reveal. Its suggestion that the
transitivity correction was missing is also corrected by the preserved unchanged
correction artifact.

## Protocol deviations and decision

Late/missing worker started posts, approximate command timing and incomplete
wrapper receipts remain disclosed. Root accepted model configuration and actual
dispatch/final board timestamps are preserved without fabricated lifecycle data.
One failed correction wake was retried in the same context within its original
budget. One metadata checksum typo was corrected without modifying first bytes.
Two automatic control-plane messages contained substantive findings outside the
board; no independent evidence credit was given until their durable reports and
board paths existed. Fresh auditors did not inherit those messages. The global
participant-table scope breach is retained above. None triggered replacement
cases, fresh first responses, a new seed or a reset budget.

Detection benefit and cost benefit are both **unmet** in this bounded pilot.
Implementation tests and additional native records do not change that result.
The useful follow-up targets are generated-goal authoring ergonomics, printable
Lean local-name support, and stronger independently justified case selection.
They are future changes, not silently added solvers or another run here.
The [snapshot manifest](pilot/MANIFEST.json) binds the preserved source-first
records. These now-exposed cases must never be reused as fresh held-out inputs.
