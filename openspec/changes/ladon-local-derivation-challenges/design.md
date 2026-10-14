# Design

## Context

See proposal.md. Investigation v1 already validates source spans, records contracts and distinguishes unresolved reviews, but schedules broad inventory first. Its fields are authored text, so it cannot interrogate a mathematical inference. No existing Fraction-based arithmetic evaluator was found in Ladon. Ordinary Lean candidate checking exists but requires an authored formal goal.

## Goals / Non-Goals

Deliver an executable falsification route for small rational implications and a consumable step/challenge workflow. Preserve v1 behavior and existing historical records. Do not parse prose automatically, prove arbitrary inequalities, implement a CAS, or claim research-paper detection accuracy.

## Decisions

1. Opt-in v2 (`init --derivations`) shares v1 source validation and finish semantics. Existing v1 plans and frozen tests remain unchanged. A concern, nonaligned/unresolved statement, different/unresolved method, or explicit derivation makes a claim require step review. Those actions precede unrelated inventory.
2. Steps preserve exact subspans, seven-field contracts, named rules, substitutions and earlier-step dependencies. They have author assessments and separate challenger outcomes. A completed formal endpoint cannot clear these obligations. Missing/uncertain/disagreeing assessments remain actionable.
3. Challenger export includes original claims, formal counterpart and all step obligations while removing prior assessments, challenge outcomes and proposed repairs. Each target carries a digest bound to the complete claim/derivation context, including assumptions and predecessor steps. A changed context invalidates previous challenges. Different reviewer labels are necessary attribution, not verified identity or enforced model isolation.
4. A bounded expression tree represents rational scalar implications. Fraction arithmetic validates every premise at a supplied assignment before claiming a counterexample to the conclusion. Failed premises are outside-assumptions; satisfying one sample is not universal support. No Python eval, imports, commands, Lean or network run in this evaluator. Semantic correspondence between the scalar interpretation and the original prose remains authored.
5. Independent workers choose small examples and controls. A fresh challenger receives a sanitized packet without the key; root saves first responses and replays proposed witnesses. This is a bounded capability exercise on authored cases with a shared filesystem, not a blind accuracy benchmark or causal improvement estimate.

## Risks / Trade-offs

- More records could again displace mathematics → suspicious steps jump ahead of inventory, and the consuming exercise must produce executable witnesses or explicit unresolved results.
- Arithmetic does not cover analytic/function-space claims → retain ordinary Lean/manual proof routes and exact residuals; never force a claim into a weaker scalar goal.
- Stronger premises, stale predecessor steps or changed constants can fabricate a successful challenge → bind the whole original context and replay witnesses against the stored arithmetic goal.
- Small examples may be too easy → report only case-specific outcomes; preserve failed attempts, controls and unanswered obligations. Stop after six fresh small cases and final engineering checks rather than expanding an evaluation campaign.

## Migration Plan

Opt in on a new plan or an explicit copied v1 snapshot by changing its version to2 and filling newly required derivations. Never rewrite a completed audit. Roll back by removing the new modules/CLI branches and retaining v1 support; plans remain readable JSON.
