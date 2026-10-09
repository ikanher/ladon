# R02 field feedback

The supplied archive passed all 15 listed SHA-256 checks and all 12 JSON files
parsed. This establishes archive consistency, not renewed Lean execution.
Selected original files and validation metadata are in `feedback-r02/`.

The report observes useful compiled lineage and a correct concurrent-source
mutation refusal. It does not retest the R01 completion or discovery failures.
Our installed 0.2.1 reproduction tests those R01 cases separately.

Two requests remain distinct from the completed repair contract:

- Allow lexical generations to advance while old compiled evidence retains its
  original generation. Current incremental update intentionally refuses retained
  lineage. Migration needs an explicit historical-evidence contract; removing
  the guard or rebinding old closures would be incorrect. Until then, a full
  build to a new index path preserves the old evidence-bearing index.
- Clarify traversal-row and distinct-node budgets. Source inspection confirms
  the SQL walk's outer limit is `max_nodes + 1`, while nodes are deduplicated
  afterward. The reported 3,001 rows / 666 distinct nodes is consistent with
  this behavior. CLI documentation now explains the units and sentinel. A
  future presentation repair may add explicit unit fields without changing
  acquisition semantics. A stored distinct-node summary cannot establish a
  sufficient path-traversal budget.

Ask the delta reviewer for a bounded next contract covering these actual
workflow needs. Do not reopen proof-interface expansion or manufacture another
mathematical uptake task.
