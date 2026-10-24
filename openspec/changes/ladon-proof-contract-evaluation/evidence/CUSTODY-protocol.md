# Held-out C custody protocol (version 1)

Status: **blocked before case admission**. This artifact freezes the admission and scoring rules only. It contains no source-family names, fault locations, labels, or answer-derived mappings. No held-out cases have been admitted and no C score may be reported from this protocol version.

## Independence and admission

C requires 12 naturally occurring source/formal pairs from six source families absent from development and source-production tracks A and B: six independently adjudicated discrepancies and six valid controls. A case is a bounded original prose fragment plus the actual corresponding formal source and enough adjacent context to interpret the relevant claim. A fragment must make at least two materially distinct claims available for candidate selection; the selected claim is recorded only in the private key. Synthetic, edited, or answer-conditioned fragments do not count as unfamiliar-source discovery. A source family is the originating paper or repository/project, not a file, theorem, or topic label.

The custodian must record provenance and exact source revisions, hashes, licenses/access basis, formal declaration identity, and why the fragment supports more than one candidate claim. Admission is allowed only when the custodian can establish the source and formal counterpart independently of the runtime authors and of any answer-informed root. If any case or source family was exposed during development, it is excluded. Uncertainty about provenance, source-to-formal correspondence, or independence excludes the case rather than downgrading the evidence silently.

Fault/control labels require a documented source-to-formal comparison prepared by the custodian before runtime freeze. A fault requires a faithful, locally pinpointed semantic discrepancy in the original pair; a control requires a justified correspondence. Planted or modified pairs must be reported as constructed fixtures and cannot count toward C. The two classes are balanced at six each. The custodian retains a private key mapping opaque case IDs to source family, target claim, formal declaration, expected class, source location, and adjudication rationale. No mapping or answer-derived symbol map enters arm inputs.

## Arm inputs and blindness

The baseline and enhanced arms receive byte-identical copies of the 12 original fragments and their actual formal source files, under opaque case IDs and randomized order. They receive no annotations, selected claim, target location, expected class, contract, symbol map, source-family label, or answer key. Each arm uses a fresh context and the same permitted tools and configuration; the first reports are frozen before the custodian opens the key. The runtime freeze must precede either arm. Any pre-report key exposure, answer-derived mapping, or non-equivalent input invalidates the blind claim and is retained as a contamination incident.

The shared checkout does not provide technical access isolation between same-user processes. Custody therefore depends on explicit role separation and access logs; any access incident is disclosed. If that separation cannot be maintained, C is labeled nonblind or blocked.

## Scoring

The fixed denominator is 12 cases per arm, including timeouts, abstentions, unsupported selections, extraction failures, and resource stops. Per case, retain first report, final report, candidate claims, extraction/fidelity errors, exact source location, interpreted discrepancy, evidence, checker attempts/results, elapsed time, peak RSS, and review history.

A true positive is a fault case with an exact source location, faithful interpretation of the discrepancy, and independently accepted source/formal evidence. A false negative is any fault case without such a confirmed result. A justified control is a control case for which the auditor supports the correspondence with evidence. A false accusation is any asserted discrepancy on a control, or any unsupported/wrong discrepancy claim on a fault case; this case-level rule prevents a wrong claim from disappearing behind a separate correct claim. Abstention is reported independently and remains in the denominator. Extraction failure and unsupported selection are also reported separately and do not erase a false accusation or missed fault.

Report TP, FP, FN, justified controls, abstentions, extraction failures, unsupported selections, coverage, time to first supported finding, checker attempts, wall time, and peak RSS by arm and case. Independent adjudicators see frozen reports and source evidence, then classify each asserted finding as supported, unsupported, or unresolved; unresolved does not count as a TP or justified control. No adjudicator may see the private key before freezing their initial review.

C's promotion conditions remain those in the parent contract: enhanced arm confirms at least 4/6 faults, justifies at least 5/6 controls, has zero false accusations, and confirms at least one more fault than baseline within equal budgets. This bounded rule is not a statistical significance claim. A blocked or contaminated C cannot satisfy it.

## Freeze record

Admission criteria and scoring are frozen by SHA-256 of this file before runtime freeze. Corpus-specific hashes are published only after a case is admitted and frozen; private key content and answer-derived material remain out of the public board. This version has no admitted corpus, so the baseline and enhanced input manifests explicitly contain zero cases and cannot be used to start scored arms.
