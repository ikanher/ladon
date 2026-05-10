# Ladon

Ladon is a host-side analyzer for Lean projects. It extracts Lean module and
declaration structure through a Lean parser helper, then reports code-quality,
proof-graph, witness, OpenSpec, and review-packet signals.

This repository is the shared home for Ladon. Downstream projects such as
`matrix-factorization` and `quux` should call this tool instead of carrying
their own copies.

## Usage

From this repository:

```bash
uv run ladon --repo-root /path/to/lean/project --root Some/Owner.lean --skip-build
```

From a target repository wrapper:

```bash
exec python3 /home/codex/projects/ladon/bin/ladon --repo-root "$PWD" "$@"
```

The bundled Lean helper is run inside the target repository's Lake environment:

```bash
cd <target-repo>
lake env lean --run /home/codex/projects/ladon/src/ladon/lean/ladon_parser_helper.lean -- <target-file>
```

## Current State

This is an extracted seed of the implementation that was developed in
`lean/matrix-factorization`. It is intentionally still Python-first while the
architecture stabilizes.

Near-term work:

- split extraction, indexing, graph analysis, witness audit, packet audit, and
  rendering into cleaner internal modules;
- add phase timing and cache keys;
- add repo-wide module DAG reporting as a first-class surface;
- convert `matrix-factorization` and `quux` to thin wrappers around this tool;
- only port stable hot paths after profiling proves they are worth moving.
