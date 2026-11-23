# Stored search batch

## Purpose

Run several declaration searches against a single stored generation with low setup cost during archive and dependency exploration.

## ADDED Requirements

### Requirement: Explicit stored batch

Ladon SHALL support an explicit stored freshness mode for a batch of name and type queries. It SHALL run without observing live source, invoking Lean or refreshing an index. A supported explicit index SHALL be queryable without an available source checkout. Batches without a freshness option SHALL retain their verified-source behavior.

#### Scenario: Archive index is available on its own

- **WHEN** an agent supplies its compatible database with stored mode and the archive checkout is absent
- **THEN** Ladon returns stored lexical results with the recorded origin and relative declaration paths

#### Scenario: An explicit current directory asserts ownership

- **WHEN** an agent runs a stored batch from an unrelated directory with only an explicit database
- **THEN** the recorded repository supplies the origin and the batch can succeed
- **AND** adding an explicit `--repo-root .` for that same request produces an ownership mismatch

#### Scenario: Live source is stale

- **WHEN** the indexed source changed and the caller selects stored mode
- **THEN** the batch describes the recorded generation with stored freshness, unchecked source status and zero live source captures

### Requirement: Coherent read and bounded publication

A stored batch SHALL report one generation identity and index path for every successful child query and the parent result. All queries SHALL observe that generation even when a writer publishes a replacement during the read. The existing batch input, result-count and byte allowances SHALL apply.

#### Scenario: A writer replaces the active index midway

- **WHEN** the batch has already pinned a read snapshot when the replacement is published
- **THEN** the batch can return the opened snapshot with stored freshness and contains rows only from that generation

#### Scenario: Batch output exceeds its allowance

- **WHEN** the encoded results exceed the selected byte limit
- **THEN** Ladon reports the limit failure without publishing a truncated output artifact
