# Named index search batch

## Purpose

Compare declaration search results from several independently maintained Lean libraries in one bounded invocation, with source and freshness provenance for each library.

## ADDED Requirements

### Requirement: Named indexes and library groups

Ladon SHALL accept an ordered, bounded set of uniquely named index selections for a common query batch. Each library SHALL resolve its own index, scope and freshness. Results SHALL be grouped in caller order with each library's index path, repository origin, generation, freshness, coverage and declaration locations where available.

#### Scenario: Two libraries contain the same qualified name

- **WHEN** the same qualified name matches in different named libraries
- **THEN** both candidates appear in their respective groups with their own source and generation evidence

#### Scenario: Libraries use different freshness modes

- **WHEN** a request selects verified mode for the local repository and stored mode for the RH index
- **THEN** each group reports its own freshness and observations and the combined result carries only per-library validation

### Requirement: Per-library outcomes

An unavailable library SHALL have an explicit diagnostic and status. Successful libraries SHALL remain available in the structured response with an aggregate partial status and nonzero exit. An available library with an empty result SHALL be distinguishable from an unavailable library.

#### Scenario: An index is missing and another library has no matches

- **WHEN** one requested index is missing, one available index has an empty result and another returns matches
- **THEN** Ladon identifies the missing index, reports the successful empty and nonempty groups, and returns partial status

### Requirement: Validated and bounded requests

A named-index batch SHALL validate the configuration before searching, reject duplicate names and enforce both per-library and aggregate output limits. It SHALL use the existing independent read and validation contract for each library.

#### Scenario: One group exceeds the per-library byte limit

- **WHEN** one library exceeds the selected byte limit and another succeeds, and the combined response fits
- **THEN** the former group reports the limit error, the latter retains its rows, and the command returns partial status with an operational failure exit

#### Scenario: Every selected library fails

- **WHEN** the configuration is valid but every library is unavailable
- **THEN** each group reports its own error, the aggregate is unavailable, and the command returns an operational failure exit

#### Scenario: Duplicate aliases

- **WHEN** two selections have the same library name
- **THEN** Ladon rejects the request before opening the indexes

#### Scenario: Individually valid groups exceed the combined byte allowance

- **WHEN** all groups fit the per-library allowance but the encoded combined result exceeds the aggregate limit
- **THEN** Ladon reports the limit failure and leaves an existing destination file intact
