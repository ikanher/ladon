# Fresh checked-application diagnostic r01

## Result

The four fresh Luna-6-medium audit arms gave the correct verdict on both constructed Mathlib source/Lean units. The ordinary-Lean control and Ladon-assisted arm each identified the omitted nonemptiness premise in unit A and justified the valid upper-ray claim in unit B. The assisted arm used native source-goal capture on both units; on B it completed the exact goal with accepted replay and trust checks. **There was no additional mathematical finding from Ladon in this two-case comparison.**

The [registration](REGISTRATION.md) and [input hashes](INPUTS.json) preceded the auditor launches. The exact delivered inputs, first source-only interpretations, final reports, scratch proofs, and native JSON receipts are retained in [inputs](inputs), [runs](runs), and [custody](custody). The 12 registered input hashes matched after all reports were frozen. A separate root oracle compiled in the pinned Lean 4.33.0 project; its two declarations depend only on `propext`, `Classical.choice`, and `Quot.sound`.

| Unit | Ordinary Lean | Ladon assisted | Native evidence |
| --- | --- | --- | --- |
| A: every natural set contains its infimum | Correct discrepancy: `S = ∅` is a counterexample; `Nat.sInf_mem` needs `S.Nonempty`. | Same correct discrepancy and counterexample. | Capture identified `Claimed S`; the bare `Nat.sInf_mem` term was rejected by type checking. No replay or trust acceptance was claimed for that rejected term. |
| B: the upper ray `{n : ℕ | a ≤ n}` contains its infimum | Correct support: `a` witnesses nonemptiness; a complete application compiled. | Same correct support, with the witness applied to the original captured goal. | Capture succeeded. `@Nat.sInf_mem {n : ℕ | a ≤ n} ⟨a, by simp⟩` completed; replay and trust both accepted with complete coverage and no `sorryAx`. |

The two controls used ordinary Lean scratch files [A](runs/a_control/Check.lean) and [B](runs/b_control/Check.lean). The assisted reports and receipts are [A](runs/a_assisted/FINDINGS.md) and [B](runs/b_assisted/FINDINGS.md). The [first interpretations](runs) precede source inspection according to the auditors' records. The root adjudication is informed; no independent or treatment-blind review was performed.

## Interpretation

There were zero false reassurances and zero false accusations in the four final reports. In unit A, native type rejection exposed a missing argument, while the mathematical refutation came from the separately checked empty-set example. A rejected candidate by itself would not prove the source claim false. In unit B, native completion adds a replayed, trust-checked certificate for the exact captured source goal, including the derived premise and conclusion transfer; ordinary Lean also established that application.

Native use was real but had friction. Unit A's first capture hit a 2 GiB cap, and one selector missed the tactic position; the later 8 GiB capture succeeded. Unit B needed three rejected term formulations before the successful fourth. The retained successful A capture and rejected completion used 8.20 and 12.73 seconds of operation time; B's retained capture and four completions used about 60.96 seconds combined. These are operation times, not total auditor effort. Peak supervised process-tree RSS in the retained operations was about 3.6 GiB. Control-arm wall time, agent tokens, preparation time, and human review effort were not measured comparably, so no cost ratio is asserted.

The exercise is a small mechanism diagnostic, not a natural-fault discovery test or a general reliability estimate. Both units were constructed, short, related, and supplied with their formal proposition and candidate theorem. The source interpretation and theorem-owner selection bottlenecks remain largely untested. On these inputs, the same LLM with ordinary Lean and the same recipe already reached the correct mathematical judgments. There is no basis here to add a production diagnostic or broad schema; the existing checked-application recipe remains the supported workflow.

## Verification and custody

- The 12 registered primary files were rehashed after the audits: 12/12 matched. Retained copies are byte-identical to those files.
- `lake env lean ../../custody/Oracle.lean` in the unit-A project compiled both oracle declarations; Lean printed only an unnecessary-`simpa` linter warning and the three permitted axioms.
- Raw native receipts show A `captured` then `rejected` (`replay.status = not-run`), and B `captured` then `completed` (`replay.status = accepted`, `trust.accepted = true`, both with complete coverage).
- [SHA256SUMS](SHA256SUMS) identifies the retained registration, inputs, oracle, first/final reports, scratch Lean files, and native receipts. Custody was withheld from auditor inputs.

**Decision:** consolidate the working recipe and native path. A further comparison needs a new, independently chosen source/Lean claim where ordinary Lean plus the same recipe has a concrete reason to struggle, or a measured effort hypothesis. This diagnostic does not alter the historical pitfall gates or complete the three planned production children.
