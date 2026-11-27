# ladon-normalized-type-fragment-search Specification

## Purpose

Let users find declarations by several pieces of a Lean type when notation spacing, theorem names, and owning modules vary across libraries.

## Requirements

### Requirement: Conjunctive type-fragment matching

Ladon SHALL accept one or more normalized fragments in a type query. Each requested fragment SHALL occur as a contiguous token sequence in at least one stored type field of the same declaration within the selected scope. Matching SHALL ignore spacing between tokens while preserving token boundaries, case and quoted contents in the indexed text. A single fragment SHALL stay within one field. Existing literal queries SHALL retain their matching and ranking behavior.

#### Scenario: Operator spacing varies

- **WHEN** a declaration contains `‖y - a‖ ^ 2` and a normalized query requests `‖y-a‖^2`
- **THEN** Ladon returns the declaration within the selected scope, subject to the result cap

#### Scenario: Fragments occur in different declarations

- **WHEN** the query requests `Measure.pi`, `∫⁻` and `∏` but no single declaration includes all three in its indexed type fields
- **THEN** Ladon returns no declaration from that population

#### Scenario: Spacing separates identifiers

- **WHEN** a fragment contains the single identifier `ab` and a declaration contains the two tokens `a b`
- **THEN** those two tokens alone do not match that fragment

#### Scenario: Lean identifier punctuation is significant

- **WHEN** otherwise matching types contain `xs.head`, `xs.head?`, or `xs.head!`
- **THEN** each fragment matches the spelling it requests, including any identifier suffix

#### Scenario: Adjacent binders and arrows retain their boundaries

- **WHEN** a stored type contains `Nat→∀ n` and the fragment contains `Nat → ∀ n`
- **THEN** the fragment matches the stored type
- **AND** `∃!` is one token while `∃ !` is two tokens

### Requirement: Conclusion-first ranking and match evidence

Ladon SHALL rank full matches by the number of distinct fragments found in a separately extracted conclusion, then by a documented stable tie-break. The ranked order SHALL precede display truncation. Each returned declaration SHALL identify the matched fragments and fields, its source location, conclusion availability and lexical authority.

#### Scenario: A later-named declaration matches the conclusion

- **WHEN** two declarations match every requested fragment but only the later-named declaration matches them all in its indexed conclusion
- **THEN** that declaration ranks first even with a result limit of one

#### Scenario: Only a source signature is indexed

- **WHEN** a declaration matches all fragments in its stored source signature and its lexical writer copied the signature into the rendered-type and conclusion columns
- **THEN** Ladon returns it subject to the cap, credits the signature once, reports conclusion evidence as unavailable and gives it zero conclusion matches

#### Scenario: A genuinely extracted conclusion equals the full type

- **WHEN** a row has extraction evidence for a conclusion identical to its full type
- **THEN** a fragment present in that conclusion receives conclusion credit

### Requirement: Bounded discovery and explicit coverage

Normalized searches SHALL support existing scopes, freshness modes and output limits through standalone and batch search. Results SHALL distinguish indexed-field matches, missing or truncated text evidence where reported by the index, and a truncated result population. They SHALL carry lexical discovery authority.

#### Scenario: Search results exceed the display cap

- **WHEN** more matching declarations exist in the selected population than fit within the result and diagnostic limits
- **THEN** Ladon marks the population truncated and reports the supported bound on the number of matches
