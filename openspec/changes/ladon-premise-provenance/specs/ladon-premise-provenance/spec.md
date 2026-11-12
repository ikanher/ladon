# Spec Delta

## Purpose

Scoped premise-origin evidence, including conclusions supplied by structures and type classes. This capability retains exact evidence scope and explicit unresolved outcomes.

## ADDED Requirements

### Requirement: Actual scoped provenance

Provenance SHALL follow observed proof terms and instantiated arguments with owner-qualified local identities through hypotheses, let aliases, field projections and instance providers. Declaration spelling or dependency-name overlap alone SHALL NOT establish a conclusion-bearing premise.

#### Scenario: Renamed structure

- **WHEN** a structure with an unrelated name contains a field of the selected conclusion type
- **THEN** the actual field projection and type are exposed without depending on the structure's name

### Requirement: Conclusion supplied as a premise

A conclusion-supplied diagnostic SHALL identify an observed route from a selected premise to the conclusion and, for the admitted projection profile, checked evidence of that exact projection. It SHALL NOT assert that the premise is necessary in every possible proof.

#### Scenario: Type class contains the result

- **WHEN** the proof projects P from an instance carrying a proof of P
- **THEN** the report names the instance parameter, field and checked projection while leaving source justification separate

### Requirement: Source justification remains explicit

Each boundary premise SHALL retain its source justification status, including declared assumption, independently established predecessor, disputed premise and unresolved origin. Source circularity SHALL require reviewed source dependency evidence in addition to a formal dependency route.

#### Scenario: Explicit conditional theorem

- **WHEN** the prose explicitly assumes a structure carrying P and concludes P
- **THEN** the conclusion-supplied fact remains visible but is not scored as a mistranslation or circular proof

### Requirement: Bounded provider graph

The graph SHALL preserve occurrence and branch scope, shared provider identities and unexpanded frontiers under declared node, depth and byte limits. A cycle or truncated traversal SHALL NOT count as proof of semantic circularity.

#### Scenario: Opaque provider

- **WHEN** a selected field is supplied through an opaque or unsupported provider
- **THEN** the report retains an unresolved frontier and does not claim complete premise provenance

### Requirement: Replay and dependency controls

Checked projection evidence SHALL preserve exact source, context, target, helper, environment and axiom identities. Discharged assumptions, unrelated fields and independently proved instance constructors SHALL be represented distinctly.

#### Scenario: Same printed local name

- **WHEN** two branches use the same local name for different premises
- **THEN** the evidence retains their separate identities and refuses a cross-branch projection

