# Evidence custody at the 2026-11-14 commit checkpoint

The remaining audit evidence is committed in topic batches without rewriting
frozen reports, manifests, source snapshots or historical outcomes. Large JSON
responses and proof-printing diagnostics remain original evidence.

A read-only check of the added SHA256SUMS files resolved paths according to
their recorded repository-relative or directory-relative form: 605 entries
matched, with no mismatches. Eight entries in the preserved
`synthetic-launch-r01/history-policy-v1/SHA256SUMS` have no corresponding file
in that historical directory. That historical manifest is retained unchanged;
this checkpoint does not assert complete historical replay closure or recreate
missing files from later versions.

The matched-pilot commit excludes local `.lake` configuration files and donor
dependency symlinks; its COMMIT_SCOPE.md records this boundary. Root-level
scratch probes and the empty files `100000-node` and `8` remain outside commits.
The evidence commits do not qualify new Ladon runtime behavior or alter the
candidate-specific 0.4.2 verification results.
