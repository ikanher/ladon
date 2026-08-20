## Context

Complete direct dependencies supplied by Lean permit fast reverse queries without executing Lean at query time.

## Goals / Non-Goals

**Goals:** exact target resolution, one indexed reverse lookup plus bounded joins, type/value distinction, ownership filters, and honest empty results.

**Non-Goals:** transitive proof relevance or semantic dependency inference from source text.

## Decisions

1. Resolve the declaration to a symbol ID, query the reverse covering index, then join source declarations in a set-oriented plan.
2. Return compiler-generated and external-frontier status rather than silently dropping them.
3. Claim absence only when every selected module reports complete dependency extraction.

## Risks / Trade-offs

- [High edge volume] → symbol dictionary, composite primary key, `WITHOUT ROWID`, and measured size gates.
- [Partial modules look empty] → explicit coverage and omission rows.
