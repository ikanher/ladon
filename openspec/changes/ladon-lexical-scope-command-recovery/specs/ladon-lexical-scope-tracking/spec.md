## Purpose

Produce lexical candidate names under the Lean 4 scope commands that real libraries use, fail closed only on genuinely ambiguous scope structure, and report exact-match counts consistent with ranked results.

## ADDED Requirements

### Requirement: Modifier-prefixed section commands are scope frames
Lexical scope tracking SHALL treat a line-initial `section` command preceded by an optional attribute block and any of the modifiers `public`, `private`, `noncomputable` or `meta` as a section frame, named or anonymous. An unrecognized modifier before `section` or `namespace` SHALL make candidate names unavailable rather than being ignored.

#### Scenario: Noncomputable section inside a namespace
- **WHEN** a file contains `namespace Real`, then `noncomputable section`, a declaration, `end`, then `end Real`, and later a `namespace Complex` block
- **THEN** the declaration's candidate name is `Real.<name>`, the anonymous `end` closes only the section, and declarations in the later block keep candidate names

#### Scenario: Exposed public section at file head
- **WHEN** a module begins with `@[expose] public section`, which is never closed, followed by balanced namespaces
- **THEN** declarations inside those namespaces receive qualified candidate names

#### Scenario: Unknown modifier
- **WHEN** an unrecognized word precedes `section` on a command line
- **THEN** affected declarations have no candidate name, and the row records the unresolved status

### Requirement: Compound end closes matching nested frames
`namespace A.B` SHALL contribute one namespace frame per component. `end X1.….Xk` SHALL close exactly k open frames whose names match from the top of the stack. Otherwise the tracker SHALL fail closed, as before.

#### Scenario: Section and namespace closed together
- **WHEN** `section IsInducing` and `namespace IsInducing` are closed by `end IsInducing.IsInducing`
- **THEN** declarations before and after that command keep correct candidate names, and earlier rows are not invalidated

#### Scenario: Mismatched compound end
- **WHEN** `end A.C` follows open frames `A` and `B`
- **THEN** candidate names become unavailable from that point, and no frame is silently popped

### Requirement: End-of-file closure is explicit
The tracker SHALL retain candidate names in safely recognized frames still open at end of file when no mismatch occurred. Unsupported unsafe frames SHALL remain unresolved. A mismatch SHALL retain the existing conservative invalidation of affected rows; EOF closure SHALL NOT repair an inconsistent scope stack.

#### Scenario: Unclosed section in a mismatch-free file
- **WHEN** a file's last `section ClosedIciTopology` is never closed and no mismatch occurred
- **THEN** its declarations receive their lexical candidate names, and implicit EOF closure is documented

### Requirement: Exact-match accounting matches ranked rows
For one name query, the match summary's exact and basename counters SHALL count the same rows that ranking labels `exact`. Alternatively, a counter's name and documentation SHALL state its narrower population.

#### Scenario: Row without a candidate name
- **WHEN** the query text equals a row's declared name and that row has no candidate name
- **THEN** the summary does not report zero exact matches while that row is ranked `exact`

### Requirement: Scope-tracking revisions refresh stored rows
The scope-tracking change SHALL advance the lexical extraction identity. Explicit `index update` SHALL re-extract rows from the recognized predecessor without source edits, preserving retained evidence through the existing history path.

#### Scenario: Companion index after upgrade
- **WHEN** a Mathlib companion index built by the predecessor extractor is updated with no source changes
- **THEN** affected modules are re-extracted, `Real.add_one_le_exp` is found by qualified name search, and prior rows are archived per history policy
