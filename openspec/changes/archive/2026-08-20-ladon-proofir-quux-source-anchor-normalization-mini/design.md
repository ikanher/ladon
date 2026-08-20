## Context

Some Quux bridge indexes already fit the compact `proofir_bridge_index` kind but
use variant source evidence fields. `sourceHash` is equivalent to Ladon's
`contentHash` for attachment checks. Nested `sourceAnchor` rows are useful but
weaker: a line hash and start line can route review, but cannot replace a full
declaration content hash unless a compatible declaration hash is present.

## Goals / Non-Goals

**Goals:**

- Normalize `sourceHash` to `contentHash` without mutating inputs.
- Normalize nested `sourceAnchor.repositoryPath` or `packetPath` into source
  path candidates.
- Add conservative source-line anchor matching.
- Keep name-only and line-anchor joins warning-oriented unless stronger source
  evidence is present.

**Non-Goals:**

- Do not compute line hashes from source files during bridge joins.
- Do not treat packet-local paths as repository truth when repository paths are
  available.
- Do not promote source anchors to proof truth.

## Decisions

1. Prefer repository paths over packet paths.

   `sourceAnchor.repositoryPath` is a better Ladon declaration-path join key
   than packet-local paths. Packet paths can be retained as metadata.

2. Introduce `source_line_anchor_decl`.

   This match kind captures declaration/path/start-line attachment at low
   confidence and warning-only status. It is stronger than basename-only for
   navigation but weaker than source-range or content-hash joins.

3. Preserve stale-hash behavior.

   If a source hash alias exists but does not match and range still matches, the
   bridge should continue to emit stale-source diagnostics.

## Risks / Trade-offs

- Line-only false positives -> Keep confidence low and warning-only.
- Path ambiguity -> Prefer repository path and keep packet path as metadata.
- Hash naming drift -> Normalize aliases in one helper before joins.
