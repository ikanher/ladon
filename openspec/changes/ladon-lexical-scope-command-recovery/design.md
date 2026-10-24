# Design

## Context

The scope tracker keeps a frame stack built from `_SCOPE_COMMAND_RE`, which matches `namespace|section|end|mutual` only at the start of a line. A candidate name is produced only while every open frame is understood (`candidate_available`). Any mismatched `end` sets `permanently_unresolved`, and `_invalidate_unbalanced_scope_rows` clears every row from the first frame still open at EOF. That fail-closed design is correct in intent, but current Mathlib syntax triggers it on legitimate files. The diagnosis and counts are in evidence/r01/FEEDBACK.md.

## Goals / Non-Goals

Goals:
- Recover candidate names for the ordinary Lean 4 scope forms that Mathlib uses.
- Keep failing closed on genuinely ambiguous input.
- Keep the operation lexical: no Lean parser, elaborator or new runtime.

Non-goals:
- Arbitrary user syntax extensions.
- Macro-generated namespaces.
- Changing lexical authority labels.

## Decisions

- **Prefixed section openers.** Accept an optional leading attribute block (`@[...]`) and any sequence of `public`, `private`, `noncomputable` and `meta` before `section`. The command must still begin a line after masking. Reject `noncomputable namespace`: the pinned Lean 4.33.0 parser rejects this form. Keep this decision tied to the current toolchain and revisit it during an explicit Lean upgrade. A modifier word the tracker does not recognize before `section`/`namespace` sets an explicit unresolved state instead of being ignored, so that a future syntax cannot silently desync the stack again.
- **Component-wise frames.** `namespace A.B` and `section A.B` push one frame per component, which keeps the qualified prefix unchanged. `end X₁.….Xₖ` closes exactly k frames, and only if their names, read top-down, equal Xₖ, …, X₁. An anonymous section frame never matches a named component. Any other shape is a mismatch and fails closed, as today.
- **EOF-open frames.** Keep candidate names in EOF-open frames when the recognized command sequence has no mismatch. Lean 4.33.0 accepts EOF-open namespaces and sections, and the user accepted this rule on 2026-10-24. Keep genuinely unsafe frames (such as unsupported mutual blocks) unresolved. After a mismatch, preserve the existing conservative invalidation of affected rows; EOF closure never repairs an inconsistent stack.
- **Counter consistency.** Compute `exactMatches`, `basenameExactMatches` and `qualifiedExactMatches` from the same row predicate that assigns `ranking.contribution = "exact"`. Alternatively, rename the counter so it clearly covers only candidate-named rows. A summary must not contradict its own rows.
- **Extraction identity.** Advance the current lexical v5 helper identity to v6 and recognize v5, v4 and v3 for update recovery, reusing the mechanism from `ladon-let-signature-recovery`. A full rebuild must not be required. The separate source-index cache algorithm also advances from 5 to 6, preventing module reuse across the scope-producer change.

## Risks / Trade-offs

- Accepting more syntax can over-accept. Each new form therefore gets a negative control: an unknown modifier, a mismatched compound end, and an anonymous section closed by a named end.
- The EOF decision trades a small recall gain for the assumption that a mismatch-free file is well-scoped. That assumption is what Lean itself enforces.
- The re-extraction cost is a one-time pass over affected modules.

## Migration Plan

Release with a new extraction identity. `index update` re-extracts rows produced by the recognized predecessor even when sources are unchanged, archiving old rows per the existing history policy. Rollback is an archived old-compatible index path.

## Local language checks

Tiny source files checked with the installed Lean 4.33.0 executable on 2026-10-24 accept compound ends, component-wise namespace ends, `public meta section`, `@[expose] public section`, and EOF-open scopes. `noncomputable namespace` exits with a parser error. These language checks guide the lexical contract; candidate names retain lexical authority.
