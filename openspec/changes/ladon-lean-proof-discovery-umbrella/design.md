## Context

Ladon already owns a canonical module DAG, source ranges, elaborated declaration
rows, family grouping, theorem-surface comparisons, process supervision, and packet
normalization. Those surfaces are report-oriented and often rebuilt per run. Active
proof work instead needs low-latency queries, exact Lean application evidence, local
goal context, and a durable explanation of why a route was accepted or rejected.

The umbrella coordinates eight children. Existing authorities remain authoritative:
Lean owns elaboration, unification, typeclass synthesis, and compiled application;
the module DAG owns import reachability; declaration source evidence owns locations;
the elaborated surface owns direct dependency/trust facts; theorem-surface changelog
owns revision comparisons; and packet evidence owns review-artifact normalization.

## Goals / Non-Goals

**Goals:**

- Answer the six `TODO.md` discovery scenarios with elaborated evidence when
  available and explicit lexical/heuristic fallback labels otherwise.
- Return useful indexed candidates in seconds without rebuilding the target for each
  query.
- Preserve scope, freshness, substitutions, unmatched premises, side conditions,
  source owners, and accepted/rejected routes in machine-readable rows.
- Keep ordinary human, editor, script, and model callers on the same CLI/protocol.

**Non-Goals:**

- No theorem proving, automatic proof repair, tactic synthesis, or production-source
  mutation.
- No claim that ranked suggestions compile until a Lean probe says so.
- No project-specific Matrix-Factorization vocabulary in Ladon code.
- No graph database, language server replacement, or complete proof-dependency graph.

## Decisions

### 1. Land the program in dependency order

The implementation order is:

```text
CLI contract ───────────────────────────────────────────────┐
index + scope -> type/semantic search -> premise routing ──┤
                                      ├-> constructor coverage -> goal probes
                                      └-> representation/scale awareness
constructor coverage + representation + route cards ------> frontier output
```

The CLI child can land independently. Search cannot claim effective scope or low
latency before the index/scope child. Constructor coverage and scale policy consume
the same difference/route schema. Frontier output lands last.

### 2. Use a persistent local index for navigation and Lean for exact matching

The public contract is a versioned persistent local query index. The alpha backend
is SQLite, stored by default at `<repo>/.ladon/index/proof-search.sqlite` beside the
repository's existing Ladon policy directory and below a dedicated disposable
subtree. It stores normalized metadata, signatures/binders, token indexes, source
ownership, aliases, fields, constructors, and dependency names. An explicit
`--index PATH` supports CI and read-only checkouts. The backend narrows candidate
sets and supports fuzzy/reverse queries; exact unification, definitional reduction,
coercion behavior, and application probes run through the pinned Lean environment
against named candidates. Ladon MUST NOT promote an indexed text match to
Lean-confirmed status, and SQLite's tables are not a public compatibility surface.

Alternative: serialize raw `Expr` values as a cross-version database authority.
Rejected because internal encodings and environment identities are toolchain-bound.

### 3. Make freshness and scope first-class query inputs

Every query records index schema/helper/toolchain/source/import fingerprints, scope
selectors, included roots/modules, and omission reasons. Incremental refresh can be
fresh only when changed modules and imported fingerprints are accounted for;
otherwise results are explicitly stale-indirect, partial, or lexical fallback.

### 4. Separate candidate generation, Lean checking, and advisory routing

Candidate rows progress through explicit stages: indexed candidate, Lean type match,
candidate application difference, optional adapter route, and optional compiled
probe. Each stage retains its own authority and failure reason. Route cards never
collapse these stages into a single confidence score.

### 5. Keep adapters and representation knowledge inspectable

Generic adapters use a versioned data registry naming exact declarations and side
condition templates. Repository-specific representation pairs, transport theorems,
scales, and range semantics live in validated repo policy and are joined to indexed
Lean declarations. Policies guide review; they do not assert theorem truth.

### 6. Preserve routes as stable review artifacts

Accepted and rejected routes have canonical identities over goal/candidate
fingerprints, substitutions, premise statuses, scope/freshness, adapters, and probe
results. Frontier output consumes those cards plus existing theorem-surface changes.

### 7. Gate utility and precision, not only schema validity

Portable Lean fixtures cover exact/near/false candidates, structure fields,
all-state versus restricted-row differences, representations, and negative adapter
cases. A large public/sibling-repository benchmark records warm-query latency and
precision but is observational, not the only acceptance authority.

## Risks / Trade-offs

- [Environment loading still dominates cold queries] → Separate cold and warm
  latency gates, reuse compiled state, and never call a rebuild an index refresh.
- [Pretty-printed signatures lose semantics] → Use them only for indexing/display;
  require Lean for exact matching.
- [Adapter suggestions become noisy] → Bound the registry, expose all side
  conditions, and preserve rejected routes.
- [Incremental freshness is overclaimed] → Fingerprint imports and downgrade status
  whenever invalidation coverage is incomplete.
- [Repository policy encodes false mathematics] → Label it as routing policy and
  require named Lean transport declarations for confirmed routes.
- [Frontier packets are mistaken for proof certificates] → Preserve authority and
  nonclaim fields through packet normalization.

## Migration Plan

1. Repair installed CLI/docs/skill examples and land index/scope schemas behind new
   proof-search commands.
2. Build portable index/freshness fixtures, then add search and difference stages.
3. Add constructor, representation, and goal-probe consumers without changing the
   existing analyzer report default.
4. Add frontier packet output only after route-card and theorem-changelog joins pass.
5. Roll back by disabling proof-search commands and ignoring/removing the disposable
   local index; existing architecture reports remain compatible.

## Open Questions

- Which Lean versions can support a long-lived query helper without protocol forks?
- Which normalized binder/type keys give the best prefilter recall before Lean checks?
- Should compiled probes be opt-in per candidate or capped top-N by default?
