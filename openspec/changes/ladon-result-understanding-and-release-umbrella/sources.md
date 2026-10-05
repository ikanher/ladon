# Source and requirement traceability

## Primary source

- Title: **Responsible Release of AI-Generated Mathematics**.
- Published date shown on source: **September 29, 2026**.
- Canonical URL: <https://agmai.org/general-sep29/>.
- Accessed for this proposal: **October 1, 2026**; the live page was checked against the user-supplied text.
- Rechecked: **October 4, 2026**, following the user's reminder of the project goal; the live page agrees with the supplied recommendations.
- Attribution: the agmai.org document; individual authorship is not inferred from the page.
- Citation key used here: **AGMAI-2026-09-29**.

This file is a paraphrased requirements map, not a redistributed copy, immutable snapshot, or claim that the website has a permanent archival identifier. Section references refer to the dated document at the URL above. Future source revisions require an explicit map update; builds and tests must not depend on fetching this page.

## Selected focus for the current milestone

The project's goal is to select practical contributions to this document, with
human understanding of mathematics as the purpose. The source mapping below is
a set of opportunities, not a requirement to implement every recommendation.

The immediate picks are **§2.B Step I.1(b)** (clear, precise conventional proof
exposition) and **§2.B Step I.4** (informal/formal links and explicit formalization
status). Together they motivate a practical workflow: review a paragraph against
its linked Lean statements, keep its hypotheses and conclusion scope intact,
check an important cited application, and revise any unsupported or overbroad
wording. A correctly stated passage is a control: the tool should not invent a
mismatch merely because some prose remains unformalized.

The captured-goal application child supports that workflow by preserving the
actual prerequisites and reporting what remains to prove. Its successful
engineering checks alone do not establish a clearer exposition or human
understanding. The next combined outcome must include an audited or improved
paragraph and disclosed formal coverage, using the fixed-epoch exposition's
transcript/average distinction and boundary-sign premise as concrete cases.
Existing design decision 10 and the application/exposition tasks own the
implementation and evaluation; this reminder creates no extra feature campaign.

**§2.B Step I.1(a)** is a related attribution opportunity: retain identifiable
sources and attributed judgments about related ideas. Search hits cannot settle
priority or novelty. Packaging and the remaining process-disclosure/community
profile work stay supporting or deferred roadmap items under the existing plan.
They do not supersede the exposition and formal-coverage task.

The community-led understanding principle in §1 and Step II guides the purpose
of these tools. Funding, scholarly legitimacy, independent repository governance,
and equitable access to frontier models require institutional actions outside
Ladon's software remit. Ladon can make material easier to inspect and discuss;
it cannot certify that these responsibilities have been fulfilled.

## Mapping

| Source location | Relevant recommendation | Ladon capability and interpretation |
| --- | --- | --- |
| §1; §2.A; §2.B Step II | Human comprehension and accountable mathematical review matter independently of producing an argument. | `ladon-proof-reading-guides` records attributed explanations/reviews; `ladon-result-understanding-evaluation` currently collects qualitative LLM usage feedback; comparative comprehension metrics are deferred per user direction. Neither certifies understanding or replaces peer review. |
| §2.B Step I.1(a) | Locate related ideas and provide appropriate scholarly attribution. | `ladon-proof-reading-guides` attaches citations, precise locators, relationship assertions, and reviews. Search candidates do not establish priority or novelty. |
| §2.B Step I.1(b) | Improve exposition, including precise statements and conventional mathematical presentation. | `ladon-proof-reading-guides` supplies an annotated reading path and separately reviewed explanations linked to exact source revisions. Automatic paper writing is outside this umbrella. |
| §2.B Step I.2 | Use independent scholarly repositories with citable identifiers, revision records, and preferably comments. | `ladon-result-release-bundles` prepares portable artifacts, version history, external identifier fields, and attributed review attachments. Repository operation, public deposit, DOI issuance, and a comment service are excluded. |
| §2.B Step I.3 | Disclose model and input/process information, time and estimated cost; retain useful original material. | `ladon-research-process-provenance` imports disclosed process records and distinguishes initial output from edited exposition. Summaries are supplied process descriptions, not access to hidden model reasoning. Missing or redacted material stays explicit. |
| §2.B Step I.4 | Formalize results, disclose partial status, connect informal and formal artifacts, and provide community formalization artifacts. | `ladon-result-claim-correspondence`, `ladon-result-formalization-dossier`, and optional `ladon-result-release-bundles` profiles cover these concerns. Community file names are examples from this source; their exact schemas and comparator behavior require separately pinned upstream contracts. |
| §2.B Step I.5 | Explain problem selection and AI involvement, including unsuccessful problems in a batch. | `ladon-research-process-provenance` separates problem/attempt inventories, selection rationale, outcomes, and population coverage. Incomplete logs cannot imply a global success rate. |

## Normative and scope boundaries

The source recommends actions to AI labs; this umbrella turns selected technical opportunities into Ladon-specific SHALL requirements. Its proposed schemas, commands, enums, byte limits, child ordering, and evaluation procedures are engineering decisions, not quotations or requirements asserted by AGMAI.

The source explicitly opposes testing advanced mathematics on inaccessible proprietary models, urges independent community leadership and funding of understanding, discourages marketing-driven releases, and calls for equitable model access. These positions are retained as source context. Ladon does not certify institutional compliance, infer endorsement of a lab or research practice, administer funding, determine scholarly legitimacy, or enforce model access. An exported dossier is evidence for scrutiny, not a responsible-release badge.

## Existing repository owners to reuse

- `docs/PRODUCT_SCOPE.md`: current workflow and authority boundaries.
- `docs/proofir-v3-query-contract.md`: bounded dossiers, derivation/navigation distinctions, and exact identity joins.
- `docs/THEOREM_CAPSULES.md`: explicit package/replay operations and portability limits.
- `openspec/specs/proofir-observation-authority-and-coverage-core/spec.md`: canonical observation/coverage semantics.
- `openspec/specs/proofir-attachment-and-link-observations/spec.md`: attachment/link evidence semantics.
- `openspec/changes/ladon-authority-safe-verified-discovery-umbrella/`: prerequisite integrity/discovery gates and readiness ownership.
- `openspec/changes/ladon-theorem-surface-changelog/`: future formal statement-change consumer; this umbrella does not create another extractor.

## Governing objective after r08

The selected motivation is community understanding, scrutiny, correction,
attribution and reuse, rather than merely easier AI production. The next proposed
activity is one real explanation-and-correction round (design decision14),
conditional on an actual author and reader need. Reading explanation/support and
ordinary checking must not depend on access to the generating model. Software
can preserve scope and evidence; it cannot certify human understanding, scholarly
responsibility or responsible release. Existing recommendation-to-capability
mappings describe retained design scope, not an active mandate to expand it.
