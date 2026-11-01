# Field reproduction and verification boundary

This packet preserves an actual installed-CLI observation from 1 November 2026.
The source bindings and installed distribution/content identities are in
`source-map.json` and `ladon-version.json`. The installed version command reports
0.3.0 while the checkout's project metadata says 0.4.0; use the bound source/content
identities, not an inferred release equivalence. No Ladon production code was
changed to produce this packet.

## Observed result

The target is
`Mf.Optimization.StochasticApproximation.gradientProcess_local_power_noise_average_clt`
in the matrix-factorization repository at `77d23ca9c`.

| Measurement | Retained result |
| --- | --- |
| Stored closure nodes | 2,242: 278 project-owned, 1,964 external frontier |
| Stored typed edges | 47,533: 10,828 type, 36,705 value |
| Extraction omissions | 0 reported |
| Refresh acquisition time | About 25.7 seconds |
| Graph request node / edge limits | 100,000 / 200,000 |
| Graph request depth / route limits | 256 / 20 |
| Internal recursive-row ceiling | 10,000, reached |
| Graph returned distinct nodes | 1,072 |
| Graph payload distinct untyped edges | 23 |
| Inherited `returned.edges` field | 73 route-edge occurrences |
| Graph truncation | Explicitly true |

The typed-edge count and untyped-pair count are different populations; do not
compute a typed-edge completeness ratio by dividing 23 by 47,533. The count-field
ambiguity is nevertheless observable: the graph's edge array has 23 entries,
while its inherited returned-edge field says 73.

`field-summary.json` records successful ingestion, authority and exact closure
identity. `field-route-graph.json` records the bounded graph projection.
Their complete stderr phase records are retained. The old projection correctly
admits truncation; the problem is inability to obtain the complete stored graph
through that route-expanded view, not a claim that this particular output said
it was complete.

## Exact reproduction commands

Run only in the trusted target checkout with its existing compiled owners and
an explicitly coordinated index writer. These commands do not build missing
Lean modules. The first command uses the recorded child and database limits.

```bash
ladon theorem lineage \
  Mf.Optimization.StochasticApproximation.gradientProcess_local_power_noise_average_clt \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --refresh missing --view summary --from trust \
  --timeout 120 --max-rss-mib 8192 --max-database-mib 1536 \
  --max-output-bytes 8388608 --format json --output field-summary.json

ladon theorem lineage \
  Mf.Optimization.StochasticApproximation.gradientProcess_local_power_noise_average_clt \
  --repo-root /home/codex/projects/lean/matrix-factorization \
  --refresh never --view graph --from project \
  --max-depth 256 --max-nodes 100000 --max-edges 200000 \
  --max-output-bytes 33554432 --format json --output field-route-graph.json
```

The target repository and compiled closure are external prerequisites, not copied
into this packet. Future source changes require a fresh acquisition and a new
receipt; an old output hash does not establish current compiled correspondence.
No database, compiled library, credential or dependency cache is bundled.

## Inspected implementation and specification mismatch

- `theorem_lineage_query.py`: `_walk_rows` expands `UNION ALL` path strings, with
  `recursive_row_limit=10000`; repeated paths revisit the same declaration.
- `theorem_lineage_projection.py`: `_route_edges(routes)` supplies graph edges;
  it deduplicates untyped pairs and retains the query's route-occurrence count.
- `theorem_cli.py`: exposes finite node/edge/route/depth limits, but no complete
  closure projection; the internal path-prefix cap is separate.
- `lean/ladon_theorem_capsule_helper.lean`: `collectRepositoryClosure` intentionally
  expands project declarations and records external boundaries.
- Archived `ladon-theorem-lineage-sql-queries` requires distinct reachability before
  bounded representative routes and forbids enumeration of all simple paths.
  The current implementation falls short of that archived behavior requirement.

## Packet verification

From the Ladon repository:

```bash
python openspec/changes/ladon-complete-lineage-closure-projection/evidence/verify.py
openspec validate ladon-complete-lineage-closure-projection --strict
```

The first command checks retained evidence identity and the numerical observation.
The second checks the planning artifacts. Neither tests the proposed implementation,
checks the Lean theorem, or certifies an axiom-complete library dependency graph.
