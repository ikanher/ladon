# Lean execution environment policy

`resolve_toolchain_context` captures a filtered selection input, resolves the
executables and existing compiled-library roots, then freezes the final process
environment before running any version inspection or source-enumeration process.
Explicit semantic, batch and scratch checks use that same environment and
repository root. Their before/after checks reject changed executable bytes,
source material, pins or compiled-library root lists.

Only `None` selects the host environment. A supplied mapping is copied before
filtering; an empty mapping means no inherited variables. Ambient Lean/Lake
selection then fails closed. Explicit executable paths remain usable and receive
the constructed `PATH` and, when compiled roots exist, derived `LEAN_PATH`.

| Key | Policy |
| --- | --- |
| `PATH` | Captured for executable discovery, then replaced by the absolute selected Lake and Lean parent directories in that order |
| `HOME`, `TMPDIR`, `USER` | Copied only when present in the selected input mapping |
| `LANG`, `LC_ALL` | Copied exactly when present; no implicit locale or value normalization |
| `LEAN_PATH` | Caller value discarded; derived from existing resolved Lake build roots, in local-root then sorted-package order |
| Every other caller key | Dropped without recording its name or value |

`ELAN_TOOLCHAIN`, loader variables, shell startup variables, Python configuration,
credentials and Git configuration variables are not forwarded. The immutable
context owns read-only copies. Direct construction with an unsupported key,
unmatched derived library path or different auxiliary environment fails without
echoing the supplied value. Direct-Lean preparation rejects a different repository
root or changed library-root list instead of modifying the bound environment.
Legacy structural operations that do not supply a toolchain context retain
sanitized ambient execution and do not acquire explicit toolchain binding.

## Auxiliary source enumeration

Git is selected once from the captured input `PATH`, before that path is replaced
for execution. Its absolute path and content identity are recorded. Git runs with
exactly the final Lean environment, including derived `LEAN_PATH`; subsequent
verification never reselects Git or rereads the host environment. Changed or
missing Git bytes fail closed before or after enumeration.

No selected Git produces an explicit `filesystem` enumeration policy. The
`git-with-nonrepository-fallback` policy retains bounded filesystem walking only
for Git's recognized nonrepository failure. It does not silently fall back after
launch failures, output limits, memory limits, timeouts or other errors. Since
locale values are preserved, an unrecognized localized nonrepository diagnostic
fails closed. Git diagnostics are not echoed by this boundary. The selected mode
records the policy, not a claim that every enumeration used Git.

## Identity and limits

Version 2 context identity hashes final environment values, resolved library roots,
auxiliary enumeration provenance, repository and selected executable identities,
pin digest, source identity, Lean release/commit and selection mode. Its canonical
encoding is Python JSON with sorted keys, compact separators, default ASCII
escaping, then UTF-8 and SHA-256. Public context metadata exposes key names,
selected paths and digests, not an environment-value dump. Discarded caller keys
do not influence those digests. Allowed values and public paths are not a secret
storage channel.

Historical stored contexts keep their original identities. Readers do not
reconstruct the private environment or upgrade old records to the version 2
construction guarantee. The context record is additive metadata inside the
existing evidence envelope, not a new ProofIR wire version.

Root-list binding does not hash every compiled `.olean` file. Git can still read
repository and user configuration from files. Filtering caller variables does
not isolate target code from files, network or inherited operating-system
resources, or from secrets placed in a requested goal, source file or allowed
path. Required isolation remains the separate execution-posture contract. These
finite regression checks qualify the exercised execution boundary; the full
security and authority exits remain separate gates.

## Maintained nonleakage regression gate

The environment regression gate injects seven synthetic discarded caller inputs.
It rejects every injected value and each opaque/disallowed key name across child
environments, diagnostics, progress output, canonical evidence, receipts,
audit/LLM/review JSON and text, stored expansion, output files, SQLite and its
nonempty write-ahead log. A positive control verifies that the scanner rejects
each marker in diagnostic, metadata-key and binary carriers. The derived
`LEAN_PATH` key remains legitimate metadata.

The gate combines real child processes for failures and resource limits, framed
fixtures for full discovery/scratch projection coverage, and ordinary installed
commands against the existing pinned Lean fixture. Real Lean cases cover accepted,
rejected and residual checks, explicit and ambient discovery with advisory scratch,
and a preflight rejection without publication. Captured results are reused across
renderers instead of rerunning Lean for each view. These fixture outcomes do not
establish behavior for arbitrary target code, file-based secrets or OS isolation.

After explicitly building `tests/fixtures/lean_integration` with its pinned Lake,
run the required gate with the selected interpreter and installed console:

```sh
LADON_REQUIRE_EXECUTION_NONLEAKAGE=1 uv run --locked pytest -q \
  tests/test_execution_nonleakage_scanner.py \
  tests/test_execution_nonleakage_failures.py \
  tests/test_execution_nonleakage_discovery.py \
  tests/test_execution_nonleakage_lean_integration.py
```

For installed qualification, use the wheel environment's `python -I -m pytest`
and set `LADON_CONSOLE` to that environment's console entrypoint; remove
`PYTHONPATH` and `PYTHONHOME`. Repeat on both supported Python versions. Required
mode fails if the fixture toolchain or Linux `/proc` RSS measurement is missing;
it never installs Lean or builds dependencies. Ordinary runs may skip real-Lean
cases when Lake is unavailable and RSS-limit cases when `/proc` is unavailable.
