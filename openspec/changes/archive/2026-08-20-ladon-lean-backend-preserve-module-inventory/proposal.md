# Proposal

The Lean backend currently uses only the modules returned by the Lean helper.
With root-scope extraction this collapses module-DAG analysis to a one-module
graph, losing the text-discovered inventory for the target namespace.

Merge Lean-extracted root module data into the existing text inventory instead
of replacing the inventory wholesale.

# Scope

- Preserve text-discovered module inventory for module-DAG analysis.
- Overlay Lean-extracted module rows for files the helper actually parsed.
- Keep declaration graph based on Lean-extracted declarations only.
- Add tests that Lean root backend retains surrounding module-DAG context.
