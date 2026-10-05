## Purpose

Connect exact informal claims to attributable formal evidence while preserving coverage, checking scope and review limitations during bounded offline inspection.

## ADDED Requirements

### Requirement: Formalization status is attributable per result
Following [Responsible Release of AI-Generated Mathematics](https://agmai.org/general-sep29/) (2026-09-29), §2.B Step I.4, the system SHALL expose per-result and per-claim formalization evidence: exact statement/targets, mapped and unmapped components, obligations, checker operations, declared assumptions, and coverage. Producer-reported completeness SHALL remain distinct from observed completeness. The source interpretation SHALL remain traceable through `../../../ladon-result-understanding-and-release-umbrella/sources.md`.

#### Scenario: Repository build succeeds with an unmapped paper claim
- **WHEN** a successful build observation exists but an inventoried paper claim has no formal target
- **THEN** the dossier shows the build and the unmapped claim separately and does not describe the whole result as fully formalized

### Requirement: Component assessments remain distinct from mathematical absence
The dossier SHALL retain component-level mapping and assessment reasons with their supplier, exact revisions and supporting references. Any required manifest extension SHALL use explicit schema versioning rather than silently broadening the current strict v1 schema.

#### Scenario: Unmapped components have different reported reasons
- **WHEN** a result contains conventional-only, unassessed, unresolved-target and reported-implication-without-checked-adapter components
- **THEN** bounded component cards identify each exact statement/component and preserve its attributed reason and evidence source
- **AND** aggregate unmapped counts do not replace these distinctions or imply that unassessed components lack a formal proof

#### Scenario: A strict formal condition supports only part of a closed article statement
- **WHEN** the selected formal target excludes an equality endpoint included in the article, or covers transcript calibration while the article also asserts average-only conclusions
- **THEN** the card exposes the hypothesis or scope difference beside the mapped component and leaves the remaining components explicitly assessed or unassessed
- **AND** neither successful checking nor a model's mapping makes the whole statement covered

### Requirement: Assumptions and external frontiers preserve origin
The dossier SHALL distinguish theorem hypotheses, observed axiom dependencies, declared external mathematical assumptions, placeholders, and unresolved frontiers with their extraction authority and coverage. Standard logical axioms SHALL NOT automatically be labeled formalization gaps. Imported declarations SHALL NOT automatically be labeled unproved. Missing transitive coverage SHALL remain unknown.

#### Scenario: Checked imports and assumed external mathematics coexist
- **WHEN** a result uses a checked imported theorem and separately declares an unformalized mathematical assumption
- **THEN** the dossier reports their distinct roles and evidence without treating both as unproved imports

#### Scenario: A lexical placeholder scan has incomplete coverage
- **WHEN** no placeholder token was observed in the scanned files but compiled dependency coverage is unavailable
- **THEN** the dossier reports the lexical observation and unknown compiled trust coverage without asserting absence of placeholder dependencies

### Requirement: Independent axes survive every projection
The system SHALL retain checker kind/outcome, environment binding, source freshness, observation state, authority, analysis completeness, correspondence review, exposition review, and attribution review separately. Stored or derived data SHALL NOT gain authority. A candidate application, theorem replay, and repository build SHALL retain their operation kinds; none alone SHALL imply informal correspondence or human understanding.

#### Scenario: Candidate application succeeds while correspondence is disputed
- **WHEN** a zero-residual candidate application and a disputed correspondence review concern the same formal target
- **THEN** both outcomes are shown and no aggregate verified badge suppresses the dispute

### Requirement: Inspection is bounded and read-only
`ladon result inspect` SHALL use explicit manifest/bundle inputs and existing CLI stream/exit conventions without implicit Lean, index rebuilds, model calls, or network access. V1 SHALL reject manifests over 16 MiB, inventories over 1,000 claims, collections over 10,000 rows, and explanatory items over 64 KiB. Compact output SHALL fit 32 KiB; pages SHALL have at most 100 rows, preserve omissions, and bind continuation to revision/query. JSON and text SHALL agree on evidence meaning.

#### Scenario: A large assumption population exceeds a display page
- **WHEN** the selected dossier has more assumption rows than fit the requested page or byte limit
- **THEN** output remains bounded, reports omitted rows or unknown totals honestly, and supplies a continuation bound to the same manifest revision and query

#### Scenario: The manifest changes between pages
- **WHEN** a cursor from an earlier revision is supplied with a newer manifest
- **THEN** the operation rejects the cursor rather than silently mixing revisions

### Requirement: Drill-down references preserve exact evidence
Compact cards SHALL prioritize the statement, assumptions, obligations, checking scope, and review gaps and SHALL provide exact references for omitted supporting evidence. Missing, malformed, stale, or environment-mismatched observations SHALL produce distinct diagnostics rather than empty successful sections.

#### Scenario: Historical replay evidence is attached to a changed theorem
- **WHEN** a stored replay observation names a different source revision from the selected formal target
- **THEN** the dossier marks the evidence as mismatched or historical and does not reuse its acceptance for the selected revision
