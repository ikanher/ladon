# Integrated consumer qualification

Task 3.1 is accepted by independent final review #1021. No production
or existing test files changed in this qualification. The umbrella planning
update keeps source-faithful discrepancy discovery as the target and separates
software qualification from measured detection benefit.

The selected 248 test modules cover native payload/reference validation,
producer identities, propagation, correspondence and investigation findings.
All **1,378 selected cases** are accounted for as passing across a preserved
partial run and its continuation. This is not an uninterrupted full-suite pass.

## Execution and the authorized budget extension

The original serial invocation had a 1,800-second outer timeout. It terminated
at 1,800.01 seconds with exit 137 and no final JUnit file. Its complete progress
log contains **566 pass reports**, no failure or skip reports. The frozen
collection and the absence of ordering plugins, conftest hooks or extra pytest
options identify a completed-module prefix. The interrupted next module's
created source-run fixture corroborates that boundary; its partial artifacts
are preserved in `interrupted-case.tar.gz`.

The user explicitly extended qualification to **60 minutes**. The extension
uses the original process start, including elapsed time, interruption and
orchestration time. The continuation selected only the **812 unfinished cases**,
including the interrupted case. It passed all 812 in **356.57 seconds** and
retained their individual XML results. No completed case was repeated. Total
elapsed test-run and interruption-recovery time was **2,223.20 seconds (37.05 minutes)**, within the
3,600-second limit. Production defaults and audit-driver clocks were unchanged.

[COVERAGE.json](COVERAGE.json), [the original command](COMMAND.json),
[original result](RESULT.json), [original progress log](integration.log),
[collection](collection.txt), [prefix and continuation selection](CONTINUATION-SELECTION.json),
[order evidence](PYTEST-ORDER.json), [budget extension](BUDGET-EXTENSION.json),
[continuation command](CONTINUATION-COMMAND.json), [result](CONTINUATION-RESULT.json)
and [XML](continuation.xml) retain the exact distinction. The first 566 have
progress-log evidence, not per-case XML. No first result was relabeled.

## Installed consumers and Rust boundary

A wheel was built offline from the current checkout and installed in a fresh
outside-checkout environment. All **533 package members** exactly match the
source snapshot, with equal source/wheel member sets. The installed import
origin is inside that environment; no global pip-installed Ladon was used.
[WHEEL.json](WHEEL.json) records the archive identity and origin. Locked dev
requirements were installed offline; the project dependencies did not change.

The [installed test invocation](INSTALLED-COMMAND.json) passed **40 tests** in
7.76 seconds, including native CLI operations, source freshness, propagation,
audit boundaries, finding projection and historical receipt compatibility.
These are additional executions of existing cases, not 40 new unique cases.
The actual wheel console additionally exercised help, checkpoint/resume,
observe/inspect/challenge/ingest/report/finalize and no-overwrite behavior.
The original checkpoint clock and prefix bytes were preserved. Empty-claims
finalization and a pending supplementary branch retained the contract evidence.

The console driver initially used incorrect audit option names and then
incorrectly expected exit 0 for a valid partial checkpoint (the actual exit is
2). Both driver versions and their outputs are preserved. The corrected driver
continued the already-created checkpoint under its original clock; no product
change or audit-clock reset was made. See [the correction record](CONSOLE-CORRECTION.json),
[console commands](console/COMMANDS.json), [console result](console/RESULT.json)
and [reproduction driver](check_installed_console.py). Constructed review labels
are attributed fixture data, not independently established source fidelity.

`cargo test --manifest-path rust/Cargo.toml --locked --offline --test contract_boundary`
passed **1 test**, confirming that the Rust consumer explicitly rejects the
contract kinds it does not support. [Raw output](rust-boundary.log) is retained.

## Inputs, provenance and limits

[RUNTIME.json](RUNTIME.json) freezes **1,393** source/test/build files and retains
all 1,223 bindings from the previous finding-projection acceptance unchanged.
The exact bytes are in `runtime.tar.gz`. Additional documentation, ledger and
historical-receipt inputs (**286 files**) were captured during the earlier
correspondence tests, before their later consumers; the capture timing is
explicit in [SUPPLEMENTAL-INPUTS.json](SUPPLEMENTAL-INPUTS.json).

One existing regression uses a hardcoded external development formalization.
Its **2,661** Lean source/toolchain/manifest files were captured before that
consumer in [EXTERNAL-REGRESSION-INPUTS.json](EXTERNAL-REGRESSION-INPUTS.json) and
an archive. It is a materialized non-git tree. Imported compiled library objects
are not copied; the ordinary extractor performs its runtime environment checks.
This is an existing source-extraction regression, not a new paper audit or a
blind discovery trial. All three live input sets verified unchanged after
execution. [ENVIRONMENT.json](ENVIRONMENT.json) records local tool identities.

All 158 frozen-test records verify, including 141 active records. Independent
review #1021 accepted the split-run accounting and installed artifact identity
after checking input hashes, archive membership, XML results and console records.
Its acceptance preserves the first-run evidence limitation and source-bound
authority limits. The review predates packet sealing; root runs the packet
verifier after sealing.

The independently sourced statement-pair gate remains open: bounded read-only
inspection found no compatible independently authored replacement in the local
material it inspected. The known matrix pair needs richer semantics than the
current Nat profile; increasing its binder cap alone is insufficient. This
negative search does not establish that no suitable pair exists elsewhere.
Planned refinement remains unimplemented. Whole-repository qualification and
quality remain separate: the general distribution gate references an absent
`tests/test_installed_cli_contract.py`, its worktree export rejects untracked
maintained inputs, and the previously recorded strict-complexity issue remains.
See [GATE-SCOPE.json](GATE-SCOPE.json).

No source-fidelity, general analytic-extraction, theorem-falsity or improved
fault-discovery claim follows. No code was committed, pushed or published.

After the final packet is sealed, `python verify_packet.py` from this directory
checks packet hashes, archived input bytes and wheel/source equality without
rerunning tests or Lean. Original commands and environment paths are retained;
replay of the external regression requires its declared development checkout.
