# Proposal

Ladon now reports module fan-in/fan-out, but it still does not identify which
direct import under a selected root accounts for most of the reachable closure.

Add root direct-import closure rows to the module-DAG summary and text report.

# Scope

- For each chosen root module, compute the transitive module count reachable
  from each direct import.
- Store compact rows in JSON.
- Render a `Root Direct Import Closures` text section.
- Keep the graph logic pure and deterministic.

# Non-Goals

- No import-cost proof.
- No Lake build timing attribution.
- No cross-repo import analysis.
