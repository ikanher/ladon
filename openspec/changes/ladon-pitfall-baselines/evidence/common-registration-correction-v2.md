# Common registration v2 execution correction

**Date:** 2026-11-12  
**Disposition:** v2 remains unchanged as historical evidence; the case 03
capability classification is not accepted under v2.

The v2 command was executed against the frozen runtime and a sparse workspace
containing only the selected case, its shared `Pitfalls` module, their reviewed
compiled artifacts, and the Lean toolchain marker. The complete receipt is in
[`qualification-runs/premise-provenance-v2-case-probe-20261112b/`](qualification-runs/premise-provenance-v2-case-probe-20261112b/).

The process returned exit code 2, left host stdout/stderr empty, and wrote a
proof-slice JSON result with `status: unavailable`, `complete: false`, and
selection `h`. The selected theorem compiled. Its helper then emitted the
registered selector-name diagnostic:

```text
error: constant not found; supply a qualified name: PitfallCases.PremiseProvenance03.h
```

The diagnostic was in the failed Lean helper's **stdout**; helper stderr was
empty. The v2 probe contract required that text in helper stderr. This is a
terminal-stream mismatch, so the result does not qualify the probe and does
not establish unsupported capability, route absence, detection, or control.
The output is retained as an unqualified observation only.

Two setup failures are also retained: the first command could not start because
the custody script lacked its executable bit; the second used an incorrectly
rooted sparse workspace and could not resolve the allowed `Pitfalls` import.
Neither is mathematical evidence. The custody script's mode was corrected to
0755 to match its shebang; its bytes and the registered argv did not change.

The proposed successor registration v3 changes the expected diagnostic stream
to stdout and records that it is post hoc to this observation. It must receive
independent review before any result is interpreted. A repeat under v3 can
qualify the revised protocol; it cannot retroactively turn this v2 observation
into a preregistered or accepted baseline result.
