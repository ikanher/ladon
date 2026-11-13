# Synthetic comparison r01 — preregistration

Status: preparation only. This packet owns a new comparison; no arm has started.
It measures controlled exposition-fault detection in one source cluster. It does
not measure natural-error discovery, general reliability or historical gates.

## Frozen population and treatment

Use exactly the five accepted v3 projections bound in the sibling
synthetic-evaluation-r01/CASESET-FREEZE.json. Each is one scored unit; variants
share one underlying proof and are not independent papers. Do not replace cases
or expose any roles, population composition, siblings, original prose, diffs,
construction records, or development certificates to auditors. Retain original
Lean statements/proofs and the crosswalk already supplied in each projection;
this evaluates interpretation with a supplied candidate owner, not blind owner
discovery. Any later supplied-obligation experiment is separately registered.

Both arms receive byte-identical selected context.md and manifest.json, all five
original capsule Lean modules and Lake/toolchain files, the unchanged complete
synthetic-workflow-r01/RECIPE.md and common dependency setup. Native capsule
semantic records are shared preparation: both may read them. The control uses
ordinary Lean and source inspection. The assisted arm additionally has this
Ladon checkout's native navigation, extraction and candidate checking interfaces.
Recipe references to Ladon mean equivalent ordinary-Lean/source steps in control;
no mathematical steps are omitted. Record actual usage, not just availability.
No adapters, hints or workflow tuning may follow exposure to evaluation answers.

## Assignment and budgets

Ten fresh contexts: one per unit per arm. Use gpt-6-luna, medium reasoning for
all ten. No conversation inheritance; no reuse of workers across units or arms.
Alternate launch order by neutral unit ordinal (odd: control first, even:
assisted first). Run sequentially for comparable resource availability. Neither
arm sees the other's work. Author, case reviewer and informed root cannot audit.
Independent adjudicators must be different from the auditors and case authors.

Each context has 20 minutes absolute wall time from first source inspection,
including tool waits, and at most 20 Lean invocations (including underlying
Ladon checker/extractor invocations). One call launching several Lean processes
counts each process; unknown counts invalidate invocation comparability. Each
process tree is capped at 12 GiB RSS and 16 MiB captured output, with at most
600 seconds and the stricter remaining unit deadline. Stop and preserve partial
results on a resource limit; no automatic escalation. Token counts are recorded
when exposed; no fabricated cap or cost. Unavailable telemetry stays unavailable.

Common pinned-package setup is performed once in a local original-capsule copy
before arm clocks start, with acquisition/cache/network/build time and memory
recorded. Both arms get independent copies of that identical prepared tree.
No live sibling checkout, symlink or environment path may supply build inputs.
Arm-specific Ladon setup/indexing counts within the assisted budget. Freeze the
actual runtime (source bytes, dirty state, Python dependencies, toolchain and
package identities) before launch. Use PYTHONPATH pointing to this checkout's
src and its .venv Python, never the pip-installed Ladon. Preparation telemetry
is reported separately and included in any descriptive total-work accounting.

## Endpoints and adjudication

Primary continuation gate: assisted produces at least one additional independently
upheld useful fault finding on a paired unit compared with control, with no new
serious false accusation on any unit. A finding needs exact source reading,
assumptions, and a valid counterexample or concretely justified source gap.
Failure to prove is unresolved. Equivalent findings phrased differently count
once. A serious false accusation asserts a supported claim is false, or claims
an invalid witness establishes a fault, without an explicit qualification.
Ambiguous passages warrant preserved alternatives and abstention when the text
does not select a reading; conditional analysis is scored on its actual reading.

Freeze every first interpretation before checking and every final first report
before answer access. Have two fresh reviewers first rate anonymized reports
against source/evidence without treatment labels, then consult the custodian's
frozen reference material. Record their independent first ratings, disagreements
and reconciled decisions. Do not alter first reports. Review every unit, including
controls, abstentions, failed checks and omissions. Report per-unit findings,
false accusations, controls, ambiguity handling and unresolved coverage. Invalid
or missing pairs remain visible and cannot support a positive primary gate.

Cost is descriptive, with no efficiency pass threshold in this study. Record
observed wall time, available tokens, ordinary and underlying Lean attempts,
native tool uptake, extraction/replay failures, resource stops, interpretation
errors, and setup/review effort. No inferential significance claim from five
related units. A gate success justifies further investigation, followed by a
separate natural-source study. Equal outcomes or a negative gate favor recipe
consolidation or interpretation work; they do not refute unused capabilities.

## Launch and exposure policy

The launch custodian copies only one projection and the registered common files
into a new unit workspace outside the repository. Never give an auditor this
registration, case freeze, archive or repository-wide browsing authority. Supply
only its per-arm prompt and recipe. Isolation is procedural unless the launcher
provides filesystem enforcement; record the actual mechanism. Deny online
research and other-agent communication. An exposure or input mismatch stops the
unit and records an incident; do not silently restart or substitute a result.

Before execution create a dated run manifest binding registration checksums,
per-unit inputs/prompts, effective model/settings, runtime and setup receipts,
start/deadline clocks and output paths. Refuse nonempty output destinations.
No mathematical arm may start until those preconditions pass. The launch
custodian may know labels but cannot send diagnostic hints. This packet does
not authorize tuning or a whole-paper run.

## Operational definitions

Registration SHA256SUMS covers every file in this packet except itself.
INPUT-IDENTITIES.json binds the upstream artifacts. The case freeze's `units`
array is the sole per-unit projection allowlist. Its INPUTS.json binds the common
original capsule file inventory. Copy only those inventories, the frozen recipe,
per-arm prompt and launch manifest. Dependency packages/build outputs are admitted
only by the recorded common setup receipt. Tool/runtime reads are limited to
pinned binaries, Python environment and checkout src/ladon; broader repository
reads and searches are prohibited. The launcher must enumerate resolved roots and
files in each delivered manifest, not supply a generic repository access grant.

An invocation is one started Lean executable process, whether direct or spawned
by Lake/Ladon; failed starts count as attempts separately. Lake compilation may
consume multiple slots. The launcher must instrument process starts and prevent
the twenty-first Lean process, including concurrent children. If the launcher
cannot enforce or account for that boundary, readiness fails before launch;
self-reported CLI-call counts are insufficient. Dependency setup is excluded
only when completed identically for both arms before their clocks start.

A useful finding identifies the exact asserted claim, a material reader
consequence and assumption-preserving evidence. Pure style complaints or a
method difference with equivalent supported claims do not qualify. Score each
claim as upheld discrepancy, supported control, warranted abstention, unresolved,
or false accusation; separately mark false accusations serious by the definition
above. Duplicate findings on one unit count once. Reviewers preserve their
independent source/evidence ratings before reference consultation, then record
reference-informed decisions separately. A third fresh reviewer resolves any
remaining disagreement with written reasoning; unresolved adjudication cannot
support the primary gate. Report all three ratings and retained dissent.
