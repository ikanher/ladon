# `ladon-sqlite-schema-rightsizing-and-accounting`

Aligns physical graph keys with queries, removes proven redundant B-trees, makes sparse indexes partial, and exposes per-object storage.

- Starts after: baselines and corrected lineage plan.
- Enables: ProofIR access paths and release.
- Excludes: in-place migration and intuition-only index removal.
- Exit: layout, plan, FK, byte-reduction, accounting, and atomic-rebuild gates pass.
