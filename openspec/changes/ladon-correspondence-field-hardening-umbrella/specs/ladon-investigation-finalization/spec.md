## Purpose

Separate preserved progress from run termination and make continuation, budget, blockers, and explicit user stopping decisions inspectable without overstating mathematical completion.

## ADDED Requirements

### Requirement: Checkpoints do not terminate an investigation
A checkpoint SHALL bind a plan, current scope, queue, clock, and observation to a new immutable record. It SHALL neither reset the start/deadline nor claim completed mathematical review or formal correspondence.

#### Scenario: Findings written while work remains
- **WHEN** findings are saved before the deadline with unresolved actionable work
- **THEN** they can be preserved as a checkpoint without becoming an ordinary finalized-run receipt

### Requirement: Finalization rechecks actual continuation conditions
Finalization SHALL re-evaluate the bound plan, current clock, and remaining work. If the outcome is continue, no successful terminal receipt SHALL be created. Recorded completion, elapsed budget, evidenced no-actionable-work blocking, or an explicit user-stop record SHALL permit an appropriately labeled terminal receipt.

#### Scenario: Retest timing replay
- **WHEN** 57.65 minutes have elapsed from a 90-minute budget and actionable work remains without a stopping instruction
- **THEN** finalization returns continue with exit 2 and retains the original deadline and pending queue

#### Scenario: Elapsed budget with incomplete links
- **WHEN** the budget has elapsed and formal links remain unresolved
- **THEN** a terminal receipt can be written as incomplete-budget while mathematical and formal completion dimensions stay incomplete

### Requirement: Blockers cannot conceal actionable work
Early blocked termination SHALL require specific evidence, next action, and an unblock condition for every remaining actionable obligation. A policy-forbidden check SHALL retain its unverified scope. Any other actionable work SHALL preserve continuation.

#### Scenario: One blocked link and an unexamined passage
- **WHEN** a missing formal capability blocks one link but permitted source review remains
- **THEN** the blocked link does not authorize ending the entire investigation

### Requirement: Stop records are attributed and immutable
An explicit stop record SHALL identify its reason, instruction reference, actor attribution, time, and bound run/scope. Such a record SHALL remain an attributed instruction, not authenticated user identity. A stop SHALL NOT imply mathematical success, and altered plans SHALL require current finalization evidence.

#### Scenario: User cancels before the deadline
- **WHEN** an actual user cancellation is recorded while work remains
- **THEN** work stops and the receipt records an incomplete user-stopped outcome without fabricated completion or elapsed budget

#### Scenario: Stale terminal receipt
- **WHEN** source scope or plan content changes after finalization
- **THEN** the earlier receipt cannot be presented as current finalization of the new state

### Requirement: Supported workflow consumes continuation results
The documented reference workflow SHALL handle continue by selecting useful available work within the original budget or recording a genuine stopping condition. It SHALL preserve report/checkpoint bytes and disclose the limit that arbitrary agent prose is not controlled by the CLI.

#### Scenario: Driver encounters unfinished work
- **WHEN** finalization refuses a premature stop
- **THEN** the reference driver records a subsequent actionable step or a new evidenced stop, without idle waiting solely to exhaust the clock

### Requirement: Compatibility and authority dimensions remain explicit
New finalization operations SHALL preserve existing v1/v2 behavior and historical v3 receipts. Permission to save an incomplete final report SHALL be distinct from mathematical completion, formal correspondence, and fresh checker replay. Status and response ingestion SHALL NOT imply that Lean was executed.

#### Scenario: Finalizing recorded formal support
- **WHEN** finalization reads prior successful native checks without replaying them
- **THEN** its receipt identifies those stored observations and does not claim new Lean acceptance
