# Design

The text extractor remains the inventory source. The Lean backend contributes
more accurate module rows and declaration rows for selected helper files.

Pipeline behavior:

1. Discover text inventory.
2. If Lean backend is selected, run helper extraction.
3. Merge `discovery.modules` with `bundle.modules`, with helper rows winning for
   duplicate module names.
4. Run module-DAG analysis over the merged module map.
5. Run declaration graph over helper declaration rows only.

This preserves root-scope speed while restoring DAG context.
