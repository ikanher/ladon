# Ladon ProofIR Bridge

The first bridge slice is intentionally separate from Ladon core.

```bash
ladon-proofir-bridge \
  --ladon-report ladon-report.json \
  --proofir-index proofir-bridge-index.json \
  --out bridge-report.json
```

## Purpose

Ladon reports structural proof-architecture context.  ProofIR reports claim,
witness, projection, and nonclaim boundaries.  The bridge joins those views and
emits reviewer-facing diagnostics.

The bridge does not:

- prove theorem truth;
- promote ProofIR statuses;
- treat Ladon edges as proof dependencies;
- treat source-hash or source-range joins as proof correctness;
- import raw evolving ProofIR packets into Ladon core.

## Input Boundary

The bridge consumes compact ProofIR review inputs, not raw ProofIR dialects.
ProofIR should own extraction and validation of these artifacts. Ladon only
normalizes and joins the small fields needed for architecture review.

Accepted bridge inputs:

- `proofir_bridge_index`;
- `proof_ir_lean_surface_bundle`, adapted into the compact bridge-index shape.

Unsupported ProofIR artifact kinds remain malformed optional input and do not
produce fabricated surfaces, claims, witnesses, or proof statuses. Non-object
JSON payloads are also treated as malformed optional input.

The compact bridge-index shape carries:

- surfaces;
- claims;
- witness endpoints;
- nonclaims;
- projection boundaries.

Quux compatibility notes:

- `sourceHash` is treated as a `contentHash` alias for source-hash attachment
  joins.
- nested `sourceAnchor` rows can supply repository path, packet path, start
  line, and line hash metadata.
- source-line anchors are warning-oriented review routes unless stronger source
  range or source hash evidence is also present.
- surface-bundle `source.sourcePath` and `source.contentHash` can backfill
  missing per-surface fields; they remain attachment metadata, not proof
  evidence.

## Current Diagnostics

The MVP emits conservative diagnostics:

- `proofir.unattached_surface`;
- `proofir.witness_endpoint_without_declaration_join`;
- `proofir.nonclaim_attached_to_root`;
- `proofir.name_only_join_warning`;
- `proofir.source_anchor_join_warning`;
- `proofir.packet_stale_source`;
- `proofir.malformed_bridge_index`.

## Trust Rule

Bridge output is review context only:

```text
Ladon structural context only; ProofIR statuses are quoted, not promoted.
```

Source-hash and source-range joins establish attachment confidence only. They
do not establish theorem truth, witness adequacy, artifact authority, or proof
correctness. Name-only joins are warning-only and never evidence.

Reviewer cards preserve quoted ProofIR metadata such as `proofTrust`,
`replayBoundary`, extractor guarantees, and source hashes when supplied. These
fields explain the external status boundary; they are not promoted by Ladon.

## Clean-Core Ladon Reports

Lean-backed Ladon reports can include an explicit
`declaration_graph.declarations` table. The bridge prefers those rows and joins
ProofIR surfaces in this order:

1. exact declaration, source path, and source content hash;
2. exact declaration, source path, and source range;
3. exact declaration, source path, and source start line from a source anchor;
4. exact declaration and module;
5. basename-only warning;
6. unmatched.

Older or derived reports may omit the table. In that case the bridge derives
fallback declaration rows from:

- `declaration_graph.edges`;
- `declaration_graph.chosen_roots`;
- `declaration_graph.top_fan_in`;
- `declaration_graph.top_fan_out`.

Those derived rows can support `exact_module_decl` joins at medium confidence.
They cannot support source-hash or source-range evidence unless the Ladon report
contains those fields explicitly.

## Atlas Workflow Snapshots

The atlas workflow can also summarize optional
`ladon_proofir_bridge_snapshot` artifacts that already contain joined bridge
rows and diagnostics. Those snapshots are downstream reviewer evidence, not the
canonical bridge input and not proof authority. The workflow maps snapshot
diagnostics into the normal `ruleId`/`level` shape and keeps snapshot statuses
quoted as external context. Source-anchor snapshot joins, including
`source_line_anchor_decl` and `root_module_source_anchor`, remain low-confidence
warning routes.
