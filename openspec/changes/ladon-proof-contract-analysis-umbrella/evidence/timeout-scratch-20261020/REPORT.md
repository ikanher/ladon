# Supervised goal scratch recovery

This implements a prerequisite of umbrella task 2.4: a killed generated-goal
worker can leave scratch Lean source that changes the Git-backed source identity
and prevents an exact-context resume. The full audit driver remains open.

## Behavior

The common supervisor reserves an exclusive per-attempt directory for the
bridge, context, route-context and probe goal workers. Internal lease metadata
travels outside the unchanged semantic job bytes; every launch strips inherited
lease metadata. Worker and supervisor check the selected root and directory
chain through no-follow directory descriptors and recorded device/inode pairs.
The worker writes and removes its own verified goal inode and bytes. Cleanup
hashing is bounded to the generated module's 8 MiB limit, and a replaced FIFO
cannot block cleanup.

The generated goal remains part of the source identity during capture and
replay. The parent removes an empty owned directory. It preserves a nonempty
owned attempt through same-device atomic quarantine outside the selected source
root, without recursive deletion or cross-device copying. Missing/replaced
ownership and relocation failure fail closed. Original timeout, memory and
output stop codes take precedence over cleanup diagnostics; a nominally
completed worker with unverified cleanup cannot produce a completed result.
There is no retry, cap increase, deadline reset or source-enumeration exemption.

## Verification

- Frozen regression before implementation: **1 failed, 1 passed**, specifically
  the timed-out worker's surviving generated source ([red.xml](red.xml)).
- Pre-change compatibility: **45 passed** ([compat-before.xml](compat-before.xml));
  source identity, freshness and composition: **53 passed**
  ([identity-before.xml](identity-before.xml)).
- Final integrated regression, ownership, implementation identity and
  compatibility: **118 passed** ([integration-final.xml](integration-final.xml)).
  The 19 ownership cases include all four
  dispatches, inherited metadata, independent/concurrent source retention,
  renamed/root/symlink/file/content replacement, quarantine preservation and
  failed relocation, oversized content, foreign FIFO, and resource-stop priority.
- One fresh actual Lean bridge goal `True` with `True.intro`: **supported**,
  replay **accepted**, trust **accepted/complete**, exact source context restored,
  source unchanged and no goal residue. It took **27.6147 seconds** under the
  original **30 seconds / 12 GiB / 8 MiB** stage bounds and one 90-second outer
  deadline ([LEAN-SMOKE.json](LEAN-SMOKE.json)). No retry was performed.
- Ordinary and prepared-source actual Lean checking: **1 passed in 62.08 seconds**;
  equal typed subjects and accepted replay/trust
  ([standalone-prepared.xml](standalone-prepared.xml)).
- Scoped Ruff, strict quality and compilation: **passed**
  ([QUALITY.json](QUALITY.json)). `uv lock --check --offline` and strict OpenSpec
  validation passed. No dependency was added.
- The previous localized-obligation packet still verifies **97 unchanged files**.
  Historical runtime identities were retained, not rehashed to authorize this code.

Final review also caught that the new goal writer was absent from the checker's
implementation digest. A separate frozen regression failed before the explicit
helper binding was added ([identity-binding-red.xml](identity-binding-red.xml)).
It now verifies that changing and restoring helper bytes changes and restores
the digest. Final integration and actual Lean verification use the corrected
bytes; earlier successful captures remain separately preserved.

The evidence directory retains before/after runtime manifests and tar snapshots.
The checker, common supervisor and implementation identity module changed among
the 1,187 existing runtime files. The final 1,192-entry snapshot additionally
records the helper, three tests and documentation. The original failing
regression and all other frozen acceptance tests remain unchanged. Independent
review is preserved in [INDEPENDENT-REVIEWS.json](INDEPENDENT-REVIEWS.json).
The distinct final auditor accepted the corrected implementation in board post
**#929**, superseding provisional **#926**, after independently checking the
final 20 portable ownership/identity tests, runtime hashes, frozen tests and
scoped quality. The auditor inspected the real Lean evidence without rerunning
Lean. The earlier green author's preparation is not independent acceptance.

## Scope and remaining gates

The nested-lifetime experiment ([NESTED-LIFETIME.json](NESTED-LIFETIME.json))
demonstrates that reaping the outer worker does not establish termination of
every child. Quarantine preserves bytes even in that case; it is not process
containment. Directory-entry syscalls retain a narrow check/use race against a
hostile same-user writer. This operates within the existing trusted local
filesystem boundary.

A failed quarantine can leave an empty owned quarantine parent, and its error
diagnostic may omit the surviving scratch location. The source bytes remain
preserved and the result stops; these are operational follow-up limits.

This is a focused regression fix. Repository-wide verification, the complete
audit driver and parent task 2.4 remain open. Parent progress remains **3/12**;
source-pair integration, refinement and detection benefit remain unestablished.
No paper-fault discovery, full-paper audit, commit or push is claimed.
