# C05 closed-proof round-trip diagnosis

The production failure is caused by truncated pretty-printing, not an invalid shifted-state proof or a failed definitional-equality comparison. This session diagnoses the cause in an isolated source copy; it makes no production repair.

## Evidence

The unchanged ordinary proof compiled again with only propext, Classical.choice and Quot.sound (`ordinary.*`). Diagnostic helpers v1/v2 retained all rejection conditions and exposed the combined condition: expression metavariables true, universe metavariables false, definitional equality true. V2 found ten natural expression metavariables; they remain after equality checking. Equality on proofs is therefore insufficient to establish a closed replay term.

V3b retained the exact printed proof. It has 132158 bytes and 22 omission tokens (`⋯`). Some omissions can be inferred during elaboration; ten expression metavariables remain. The pinned Lean source defines pp.maxSteps with default 5000 in Lean/PrettyPrinter/Delaborator/Options.lean. Basic.lean emits an omission when that step budget is exhausted. Lean/Elab/BuiltinTerm.lean's elabOmission warns and elaborates the token as a hole. Setting pp.all does not override the step budget.

V4b changes only pp.maxSteps to 200000 in the isolated helper's printing options, apart from writing the printed text to this evidence directory. It preserves the original closure, metavariable, equality, replay and trust checks. The printed proof has 2947873 bytes and zero omission tokens. The same corrected C05 term now completes with accepted independent compiler replay and the three permitted axioms (`C05d4b-complete.json`). Completion took 47.25 seconds and peaked at 5631717376 bytes RSS (about 5.24 GiB). Ordinary compilation took about 1.9 seconds. These measurements describe this probe, not a general benchmark or a justified production default.

## Scope and failed attempts

All commands use the pinned Lean 4.33.0 toolchain, retained local project/import cache, a new one-hour session, 600-second operation limits, 12 GiB RSS and 16 MiB output limits. DO.py supplies the isolated copied package via PYTHONPATH. The project is the retained N.3c working project; no donor checkout is used. The supplied source interpretation and proof are known development material.

V3 failed to compile because its diagnostic IO call used an unavailable liftIO identifier; v3b corrects that instrumentation. V4 failed to compile because Options.setNat is unavailable; v4b uses Options.set. These failed instrumentation attempts and receipts are retained. They are not additional product failures. Native instrumented rejection, ordinary success and the successful single-option experiment establish the diagnosis; no independent reviewer or new discovery experiment was involved.

The production helper and shared printer hashes remain unchanged against BASELINE-IDENTITIES.json. Helpers and printed texts are retained for the diagnostic variants; the full copied package remains under temp/c05-roundtrip-diagnosis-r01/src. This evidence is local and depends on the retained project/dependency cache, not a standalone replay distribution. Previous N.3 reports remain unchanged historical evidence.

## Next implementation boundary

The next fix should make proof serialization explicitly account for the printer budget and report truncation directly. Merely relying on pp.all permits loss of proof content. The successful 200000 setting is a qualification probe, not evidence that this number is sufficient for arbitrary proofs. Preserve finite resource bounds, reject omitted/unresolved content, and keep all existing closure/equality/replay/axiom guards. A central generic implementation needs a small regression plus negative controls for missing premises, placeholders, incompatible contexts and forbidden dependencies. No stochastic-case-specific branch is justified.

This is distinct from the earlier unconfirmed auxiliary-declaration export hypothesis: this C05 probe passed replay without any export change. It establishes a concrete serialization limitation and a viable bounded repair direction, not improved detection from prose.
