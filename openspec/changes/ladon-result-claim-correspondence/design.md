## Context

Parent: `../ladon-result-understanding-and-release-umbrella/`. Source: [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.4. The user deferred metrics in favor of actual LLM usage feedback.

## Goals / Non-Goals

**Goals:** strict, bounded manifest validation; exact declared revision references; current versus historical attributed review observations; a useful installed artifact-only command.

**Non-Goals:** invoking Lean, proving informal correspondence, authenticating reviewers, or exiting upstream authority gates. Canonical target resolution is the gated second milestone; the completed offline milestone retains its original behavior.

## Decisions

The v1 manifest owns `claims`, `targets`, `links`, and `reviews` as closed collections. Claims carry supplied statements, component IDs, and document locators/digests. Targets carry declaration names and source/environment identities, with optional artifact-qualified subject references. Links reference existing claims, components, and target IDs. Reviews bind a link digest, claim revision, and target revision set; their assertions remain self-attributed.

SHA-256 revisions use canonical compact UTF-8 JSON with sorted keys, no ASCII escaping or non-finite numbers, and a kind-specific domain prefix. Only the revision field of the object being hashed is omitted. Revision mismatches reject input. Review bindings that differ from current subjects remain historical rather than invalidating an otherwise well-formed history.

The runtime shape checker supports only the finite JSON-schema vocabulary used by this bundled schema; conformance tests compare it with the development-only JSON Schema validator. No general schema framework or runtime dependency is introduced. Input is a regular file capped at 16 MiB, with duplicate keys, invalid Unicode, deep nesting, and non-standard JSON rejected. Strings have UTF-8 byte limits as well as character limits.

The CLI returns bounded counts and review observations. All canonical links remain unresolved with `canonical-evidence-not-loaded`. Validation success means schema, declared identity, and reference integrity only. Current review status does not imply truth, human review when authored by a model, or reviewer authentication. The installed command is verified outside the checkout with subprocess/network activity forbidden in the test harness.

## Risks / Trade-offs

- [Producers must compute revisions consistently] → document the domain/canonicalization and expose a small Python helper with fixed-vector tests.
- [Review history is mistaken for current approval] → bind link and subject revisions and show historical counts explicitly.
- [The command appears to resolve Lean evidence] → always report unresolved canonical targets; defer the resolver and full child exit.

## Remaining integration

The full target resolver and child receipt require compatible authority-safe and verified-discovery exits. The offline milestone can pass independently and does not satisfy those prerequisites.

## Canonical target resolution (second milestone)

`ladon result resolve MANIFEST --artifact ENVELOPE.json` accepts repeated explicit
local ProofIR v3 envelope files. It starts no Lean, network request, registry,
index refresh or publication. The existing envelope/batch owner validates the
complete supplied population before selection. Inputs stay bounded by the existing
ProofIR per-artifact/batch contracts; target/review output keeps the manifest's
32 KiB compact ceiling and reports omissions.

A target must explicitly name its artifact-qualified declaration subject. Name
search cannot manufacture this reference. Reuse `candidate_type_evidence` to
validate the rendered type against the canonical declaration's structural identity.
Require exact name and supplied type text, the canonical environment digest and
supported toolchain descriptor, plus an exact artifact-qualified source-map anchor
with matching source path/content digest. Source-map association uses the existing
attachment resolver's environment/fingerprint contract. Preserve unresolved and
ambiguous evidence; mismatched type, environment or source bindings report stale
relative to the supplied manifest. Supplied `projectRevision` remains attributed
metadata: the source-map contract does not independently observe Git history.

Resolution establishes exact stored target association only. It does not replay
checks, establish current working-tree freshness, or apply a candidate check's
acceptance to the informal claim. Correspondence reviews retain their existing
revision currency. Files that are explicitly supplied but malformed fail the
operation before success output; missing optional references remain unresolved.
The frozen fixed-epoch article/archive baseline stays unchanged and is used as a
negative case for absent canonical references, rather than filled with invented
subjects or environment receipts.
