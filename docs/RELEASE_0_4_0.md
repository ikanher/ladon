# Ladon 0.4.0 development snapshot

This local development snapshot collects the contract-analysis work and the
Mathlib navigation corrections since 0.3.0. It remains an alpha snapshot with
explicit capability and qualification limits.

## Changes

- Bounded mathematical contracts: source-attributed inputs, native ProofIR
  validation, conditional propagation, local obligations, rational witnesses,
  checked branch probes and refinement with distinct source-cited and proposed
  repair branches. See [mathematical contracts](PROOF_CONTRACTS.md) and
  [refinement](CONTRACT_REFINEMENT.md).
- Investigation findings and finalization retain incomplete, attributed and
  checked outcomes separately. Source-goal and theorem-capsule helpers retain
  finite execution bounds and explicit source identity.
- Lean execution defaults to a 12 GiB process-tree RSS limit. Memory-stop
  diagnostics instruct agents to report back instead of silently raising the
  cap. Deleted tracked sources are fingerprinted according to the current
  working tree while unsafe links and observed read failures remain errors.
- Lexical navigation recovers modifier-prefixed sections, compound scope ends,
  escaped names, safe EOF-open scopes, and signatures with same-line `where`
  bodies. Exact-match counts include basename rows without candidate names.
  Common help output and installed CLI contract coverage have been refreshed.

## Migration

Use this checkout explicitly while developing Ladon, and record `ladon version
--json` for reproducible observations. The shipped skill and the shared
`codex-skills/ladon` guidance describe the current workflows.

Run `proof-search index update` to refresh recognized v3/v4/v5 lexical indexes
to extractor v6. Retained evidence is archived through the existing history
policy; an unchanged subsequent update is a no-op. Follow `full-build-required`
for unsupported bases. The separate source-index algorithm also advances to v6
so its module cache re-extracts names. Recapture source-goal evidence when helper
identity changes. No Lean/toolchain upgrade is included.

## Verification and limits

The staged 0.4.0 package candidate built an sdist and wheel, installed outside
this checkout, and passed **41 installed CLI contracts**. The gate completed in
22.56 seconds under its 600-second/12-GiB bound. Another 28 focused help,
version, release-selection and evaluation-corpus tests passed; the lockfile
check and both skill validators pass. The shared Ladon skill is committed as
`bf84cfa` in `codex-skills`.
[Release receipts](../openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/development-snapshot-0.4.0/release-record.json)
identify the tested candidate tree. Later additions contain release notes and
retained receipts; the packaged sources are unchanged.

The [scope-recovery qualification](../openspec/changes/ladon-lexical-scope-command-recovery/evidence/r02/REPORT.md)
records 248 passing affected contracts and an independently audited change.
On the pinned 240,583-declaration Mathlib population, missing candidate names
fell from 8,024 to 119. Both reported qualified theorem queries now return exact
matches. The disposable rebuild took 73 seconds and about 80 MiB sampled peak
process-tree RSS.

The broader [implementation qualification record](../openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/deleted-source-identity-20261023/REPORT.md)
retains a full run with 4,885 passed, one skipped and two failures reporting
source-tree identity drift in the live sibling workspace. Both failed cases
passed in isolation and under a read-only source snapshot. The subsequent full
snapshot run was stopped when work was reprioritized. A complete passing strict
gate on the final 0.4.0 tree is therefore unestablished.

Contract evaluation and general exposition-error detection remain open gates.
Lexical navigation does not include every compiler-generated declaration, and
source headers may omit elaborated section context. Authored interpretations,
checked formal support and independently reviewed source fidelity remain
distinct. Detection benefit remains unestablished.
