## ADDED Requirements

### Requirement: Declaration and audit integrity is an integration overlay
The declaration-and-audit integrity capability SHALL extend the canonical
declaration rows owned by `ladon-declaration-source-evidence`, SHALL preserve
Lean-confirmed identity and result authority owned by
`ladon-elaborated-declaration-surface`, SHALL extend the audit rows owned by
`ladon-lean-audit-command-surface`, and SHALL route final module roles through
the facade classification owned by `ladon-common-layer-and-facade-quality`.
It MUST NOT create a second declaration table, audit-command model, Lean result
model, facade taxonomy, or source-attachment authority.

#### Scenario: Lexical evidence is enriched in place
- **WHEN** the text source index safely derives namespace context, declaration modifiers, or an audit subject candidate for an existing canonical row
- **THEN** Ladon attaches that evidence to the owning source-index and audit rows with their stable identities instead of emitting a parallel declaration or audit surface

#### Scenario: Lean evidence is available
- **WHEN** the existing elaborated backend confirms a declaration identity or audit result
- **THEN** Ladon attaches the Lean-owned result separately with `lean_environment` authority and preserves the underlying lexical candidate and its `lexical_text` authority

### Requirement: Namespace-aware lexical declaration candidates
The comment- and string-safe source index SHALL retain the safely recognized
namespace stack, declaration kind, supported modifiers, privacy or locality,
source range, and normalized declaration-block hash for each supported lexical
declaration. It SHALL derive a candidate fully qualified name only while the
lexical scope state is unambiguous. Such a name MUST be labeled as a lexical
candidate and MUST NOT be represented as a Lean-resolved declaration identity.

#### Scenario: Nested namespace declaration
- **WHEN** a supported declaration occurs inside safely balanced nested namespace commands
- **THEN** its source row records the namespace stack and one candidate fully qualified name with `lexical_text` authority and a nonclaim that Lean name resolution and elaboration were not performed

#### Scenario: Section does not create a namespace
- **WHEN** a declaration occurs inside a named section nested within a safely recognized namespace
- **THEN** Ladon preserves the section as lexical context but does not insert the section name into the candidate fully qualified declaration name

#### Scenario: Ambiguous lexical scope
- **WHEN** unsupported syntax, an unbalanced namespace command, or another ambiguous scope transition prevents safe fully qualified name construction
- **THEN** Ladon retains the source-located declaration row with unresolved candidate-name status and MUST NOT guess a namespace or fully qualified name

#### Scenario: Declaration-like comment or string
- **WHEN** namespace commands or declaration text occur only inside comments or string literals
- **THEN** they do not change lexical scope state and do not create declaration candidates

### Requirement: Conservative cross-file collision candidates
Ladon SHALL group cross-file declaration collision candidates only when two or
more non-private, non-local source rows have the same safely derived candidate
fully qualified name. Complete canonical membership SHALL remain addressable from
the source index through bounded inspection when the total is known. A projected
group SHALL retain exact coverage or explicit unknown-total state plus bounded
member source anchors, module identities, lexical authorities, and witness
references. A collision
candidate MUST NOT be described as a Lean environment error, compilation
failure, theorem defect, or proof conflict without separate Lean-owned
evidence.

#### Scenario: Same candidate identity in two modules
- **WHEN** two distinct source modules contain non-private declarations with the same safely derived candidate fully qualified name
- **THEN** Ladon emits one deterministic collision-candidate group that cites both canonical declaration rows and states that coexistence has not been confirmed by Lean

#### Scenario: Equal basenames in different namespaces
- **WHEN** declarations have the same local basename but safely derived candidate fully qualified names in different namespaces
- **THEN** Ladon does not group them as a fully qualified name collision

#### Scenario: Private or local declarations repeat
- **WHEN** lexically private or local declarations repeat the same written name in different modules
- **THEN** Ladon preserves their individual source rows but excludes them from public cross-file collision promotion

#### Scenario: Collision witnesses exceed the display bound
- **WHEN** one candidate identity has more member rows than the configured witness bound
- **THEN** Ladon reports exact total, visible, and omitted member counts and does not present the bounded sample as the complete group

### Requirement: Duplicate-source evidence remains distinct from identity evidence
Ladon SHALL expose exact file-content hashes, normalized declaration-block
hashes, and normalized source-shape similarities as separate evidence kinds.
Hash or shape equality MUST NOT by itself establish equal Lean declaration identity,
equal theorem statements, equal proofs, a collision, or a generator defect.

#### Scenario: Exact declaration-block duplicate
- **WHEN** two canonical declaration rows have equal normalized declaration-block hashes
- **THEN** Ladon records an exact-block duplicate candidate with both source anchors and hash-method identity while retaining lexical nonclaims

#### Scenario: Exact file duplicate
- **WHEN** distinct module paths have identical source-content hashes
- **THEN** Ladon records an exact-source duplicate candidate without claiming that Lean loads both modules, assigns the same declarations, or rejects either file

#### Scenario: Similar shape with different bytes
- **WHEN** two declaration blocks share a normalized source shape but have different exact hashes
- **THEN** Ladon labels the relationship as shape similarity and MUST NOT upgrade it to exact duplication

### Requirement: Selected-context collision registration
Collision review registration SHALL require an inspectable relationship showing
that the candidate members can occur in one selected module-import context,
such as closure membership, a shared importing facade, or another canonical
module-graph witness. Inventory-wide name equality without a selected-context
join SHALL remain an inventory candidate and MUST NOT be registered as a
co-reachable shard collision. This capability SHALL emit only the canonical
producer row and its evidence, coverage, authority, nonclaims, and inspection
action key; complete review-region synthesis remains owned by
`ladon-report-coverage-and-snapshot-integrity`.

#### Scenario: Shared importing facade
- **WHEN** one selected facade or closure contains imports that expose both modules in a lexical collision-candidate group
- **THEN** Ladon SHALL register a co-reachable collision producer row only with canonical declaration and `module_import_graph` witness references, without emitting a complete review-region object

#### Scenario: Disconnected inventory candidates
- **WHEN** equal lexical candidate names occur in modules with no available selected-context coexistence witness
- **THEN** Ladon preserves the inventory collision candidate but emits no co-reachable collision registration

#### Scenario: Partial graph evidence
- **WHEN** projection or phase truncation removes the rows needed to establish coexistence
- **THEN** Ladon marks selected-context status unavailable and MUST NOT infer coexistence from module names or source ordering

### Requirement: Continuation-aware audit command parsing
The existing audit-command scanner SHALL recognize supported multiline
`#check` and `#print axioms` forms when the subject occurs on a safe
continuation line. The canonical row SHALL retain the complete bounded command
range, exact supported subject text, stable command identity, containing
module, backend, and authority. Unsupported continuation syntax MUST remain a
source-located unparsed audit row rather than being silently discarded or
guessed.

#### Scenario: Check subject on the following line
- **WHEN** a supported `#check` command places one bare declaration subject on a safe continuation line
- **THEN** Ladon records the subject and a source range spanning the command keyword and subject with `lexical_text` authority

#### Scenario: Axiom-query subject on the following line
- **WHEN** a supported `#print axioms` command places one bare declaration subject on a safe continuation line
- **THEN** Ladon records lexical axiom-query intent without claiming a captured axiom set or Lean resolution

#### Scenario: Unsupported multiline subject
- **WHEN** a multiline audit command contains syntax that the bounded scanner cannot safely delimit or classify
- **THEN** Ladon retains an unparsed command row with a structured reason and MUST NOT invent a referenced declaration

#### Scenario: Commented continuation
- **WHEN** apparent audit subjects occur only in comments or string literals after a command-like token
- **THEN** Ladon does not treat those bytes as a parsed audit subject

### Requirement: Audit evidence precedes final facade role classification
Final module-role classification SHALL consume both declaration and canonical
audit-command evidence. A declaration-empty module containing supported audit
commands SHALL receive the evidence-backed `audit_surface` role. It SHALL receive
`command_only_audit_facade` through the existing facade owner only when independent
import/public-aggregation evidence satisfies that owner's facade predicate. An
audit surface assigned `command_only_audit_facade` MUST NOT simultaneously be
classified as a generic `pure_barrel`. Generic public-facade pressure SHALL be
suppressed for that role unless independent non-audit evidence satisfies the
owning rule.

#### Scenario: Command-only audit facade
- **WHEN** a module imports reviewed owners, contains supported audit commands, and contains no declarations
- **THEN** its final roles include `audit_surface` and `command_only_audit_facade`, exclude `pure_barrel`, and route audit navigation instead of generic public-API pressure

#### Scenario: Mixed audit and declaration module
- **WHEN** a module contains both a declaration and supported audit commands
- **THEN** Ladon preserves both surfaces but does not label the module command-only

#### Scenario: Isolated command-only audit surface
- **WHEN** a declaration-empty module contains a supported audit command but lacks the import or public-aggregation evidence required by the existing facade predicate
- **THEN** its final roles include `audit_surface` but exclude `command_only_audit_facade` and `pure_barrel`

#### Scenario: Audit-like filename without commands
- **WHEN** a declaration-empty module has an audit-like filename but contains no supported audit command
- **THEN** its role is determined by ordinary source and graph evidence and MUST NOT be inferred from the filename

### Requirement: Audit subject ownership preserves candidate and result authority
Ladon SHALL keep any text-backed audit attachment to a unique lexical
declaration candidate explicitly at candidate status and `lexical_text`
authority. The containing audit module, candidate referenced owner,
Lean-resolved owner, command backend, result
backend, and result authority MUST remain separate fields. Candidate attachment
MUST NOT change an unavailable Lean result into a resolved or complete result.

#### Scenario: Unique lexical subject candidate
- **WHEN** a bare audit subject matches exactly one safely derived candidate declaration identity in the fingerprint-matched source index
- **THEN** Ladon records a lexical referenced-owner candidate and preserves the command result as unavailable under the text backend

#### Scenario: Ambiguous lexical subject candidate
- **WHEN** an audit subject matches several lexical declaration candidates or requires unsupported name resolution
- **THEN** Ladon retains the command with ambiguous or unresolved candidate status and does not choose an owner by basename, path order, or import popularity

#### Scenario: Lean resolves the subject
- **WHEN** the existing Lean audit enrichment resolves the command subject
- **THEN** Ladon records the Lean-resolved declaration, owner, backend, toolchain, and result authority separately without erasing or upgrading the lexical row

### Requirement: Deterministic and coverage-bearing integrity rows
Ladon SHALL assign namespace candidates, collision groups, duplicate-source
groups, multiline audit rows, and role attachments stable identities and
deterministic ordering for equivalent source bytes, scope, source-index schema, and explicit
configuration. Every bounded member collection SHALL report visible, total,
omitted, and completeness state and SHALL preserve resolvable references to its
canonical rows.

#### Scenario: Equivalent repeated text analysis
- **WHEN** the same portable sources and explicit metadata are indexed twice with no source drift
- **THEN** candidate names, hashes, collision groups, audit identifiers, final roles, ordering, coverage, and normalized machine output are identical

#### Scenario: Canonical evidence reference is unavailable
- **WHEN** a projected integrity row cannot resolve a required declaration, audit, or graph reference
- **THEN** Ladon marks the relationship unavailable and MUST NOT publish it as a complete collision or ownership result

### Requirement: Portable positive and negative integrity gates
Required declaration-and-audit integrity gates SHALL use tracked,
target-neutral fixtures and SHALL complete on the text backend without running
Lake, Lean helpers, version control, target initializers, or a target build.
Mutable external repositories MUST remain optional, read-only observational
evidence with source and analyzer fingerprints.

#### Scenario: Portable positive fixture
- **WHEN** a tracked fixture contains nested namespaces, a cross-file candidate-name duplicate, an exact block duplicate, an exact file duplicate, a co-reachable pair, multiline check and axiom commands, and a command-only audit facade
- **THEN** the required gate verifies source anchors, lexical authority, separate duplicate evidence kinds, selected-context joins, parsed subjects, audit role precedence, stable identities, and all required nonclaims without launching an external process

#### Scenario: Portable negative fixture
- **WHEN** a tracked fixture contains equal basenames in different namespaces, repeated private names, declaration-like comments and strings, disconnected candidate members, ambiguous audit subjects, unsupported multiline syntax, and an audit-like filename without commands
- **THEN** the required gate verifies no false fully qualified collision, no private-name promotion, no comment or string rows, no invented coexistence or owner, structured unparsed status, and no filename-based audit role

#### Scenario: Optional live repository observation
- **WHEN** declaration and audit predicates are observed on a mutable large Lean repository
- **THEN** Ladon records source fingerprint, dirty state, analyzer identity, coverage, and moving counts and MUST NOT make that repository or its current cardinalities required test authority
