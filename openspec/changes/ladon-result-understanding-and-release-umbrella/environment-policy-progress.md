# Baseline-driven requirements and execution boundary progress

The fixed-epoch baseline now has explicit acceptance cases in the proposal,
design, tasks, claim-correspondence, dossier, guide and evaluation specs:

- per-component reasons instead of only an aggregate unmapped count;
- strict/closed and transcript/average-only scope differences;
- separate manuscript, pinned archive and working-tree identities;
- conditional-result/counterexample reading order;
- immutable baseline inputs and explicit later comparison results;
- nonexistent supplied targets remaining unresolved after offline validation.

The current strict manifest v1 has not been broadened. Any required component
assessment extension must be versioned in its implementing child.

## Implemented prerequisite repair

Candidate `27b57a3007557bf6936288ce8aee745f0c29d600` fixes two reproduced
execution-boundary bugs:

1. `environment={}` previously selected the host environment because the
   resolver used a truthiness fallback. It now means an explicitly empty input;
   only `None` inherits host keys. Ambient lookup cannot use a host PATH that
   the caller did not supply.
2. Directly constructing a toolchain context previously bypassed the resolver's
   environment filtering. Unsupported keys now fail before use, without their
   names or values in the error.

The allowlist has one owner reused by toolchain resolution, ambient direct-Lean
preparation and source-enumeration filtering. The existing key set and locale
behavior are retained. See [the environment policy](../../../docs/EXECUTION_ENVIRONMENT.md).

Fourteen new regression cases cover the two boundary failures, direct
construction, ten discarded-key examples, immutable ownership and locale-bound
identity. The initial run reproduced three failures; the patched focused suite
passes 67 tests, and each installed Python runtime passes 136 relevant tests.
Fresh ordinary installed Lean 4.32.1 acceptance and semantic rejection pass on
the portable fixture. Four synthetic caller variables are absent from compact
output, canonical stored artifacts, receipts, stored JSON/text and registry
bytes. These observations do not establish arbitrary target-code isolation.

The frozen exposition baseline was replayed without changing any baseline
files. Both installed runtimes retain all nine outcomes. Successful stdout is
byte-identical; rejected cases preserve exit class and diagnostic code. See
[the comparison record](baseline-environment-comparison.json).

The full clean-candidate gate passes 2,372 maintained tests and 29 installed
CLI contracts, plus strict quality, compilation, build and distribution checks.
The required benchmark passes 17/17 cases with zero correctness or stability
failures. Exact commands, artifact digests
and current candidate identity are retained in [apply-run-state.json](apply-run-state.json).
Local raw captures are under `/tmp/ladon-execution-environment-f7qi6997`.

## Reopened work

Prerequisite task **3.2 is reopened**. Direct-Lean preparation derives
`LEAN_PATH` after base-context construction, while VCS enumeration selects its
own utility and filtered host environment. The existing base context and
executable checks do not establish one unchanged final environment across
those operations. Next work must bind the final launch environment and make
auxiliary process provenance explicit before declaring that contract complete.
Tasks 3.1 and 3.5 remain open for that qualification and broader nonleakage
coverage; this patch does not issue a full authority exit.

Current counts are result umbrella **9/50**, claim child **5/8**, and prerequisite
umbrella **38/76**. Earlier 39/76 records remain historical. No dossier/guide
availability, checked exposition correspondence, measured understanding benefit
or release qualification is claimed.
