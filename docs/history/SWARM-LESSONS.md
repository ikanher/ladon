# Swarm lessons

This is a first-hand record of the multi-agent ProofIR v3 experiment. It is
deliberately about observed behavior, including failures, rather than a general
argument for agent swarms.

## What helped

### Durable communication beat chat memory

The SQLite bulletin board gave each finding, contract, test freeze, assignment,
and completion a stable identity. Posts could cite and refute earlier posts, and
the human observer could follow the work without reconstructing hidden agent
messages. Storing model family and reasoning effort on the post made authorship
meaningful instead of presenting every worker as an opaque agent ID.

The board was especially useful across long runs and context compaction. The
current task state remained inspectable even when conversational summaries were
incomplete.

### Distinct roles exposed different failure modes

The most useful separation was not “many implementers.” It was tension between
roles:

- a test author froze observable behavior before production edits;
- a green implementer worked against that frozen contract;
- a pedantic auditor looked for false-green cases outside the frozen examples;
- a mathematician specified AND/OR hypergraph semantics and adversarial cases;
- a supporter and skeptic independently argued whether ProofIR earned its
  complexity;
- a documentation scout looked for claims that exceeded implementation.

This produced real corrections. The pedantic SQLite pass found that rebuilding
after a resolved environment manifest could violate a transient foreign-key and
`CHECK` state even though the frozen projection suite was green. The clean-break
review rejected a first “green” implementation that merely renamed legacy
tables to `retired_*`. The derivation discussion separated a navigation path
from a complete conjunctive proof slice before those representations became a
public contract.

### TDD reduced negotiation ambiguity

A frozen test path and digest was a better handoff than prose such as “implement
the schema.” It made ownership clear and prevented an implementer from silently
weakening the test while making it pass. Keeping superseded test revisions was
also valuable: a strengthened contract did not erase the weaker contract that
had produced a false green.

### Human-readable tags and threads were useful

Topics, tags, reply links, states, and model labels made the board substantially
easier to follow than raw inter-agent messages. Tags are a more reliable
compression mechanism than inventing terse prose abbreviations because they
remain searchable and have stable meanings.

## What did not work well

### Posting is not collaboration by itself

Initially, agents mostly published isolated reports to the root. They did not
read or challenge one another. “Use the board” was insufficient; assignments
had to name public questions, relevant peers, and the posts that required a
response. Useful swarm behavior began only when the supporter, skeptic,
mathematician, and auditor were asked to engage the same claim from different
directions.

The protocol therefore needs an explicit rule: before completing a task, a
worker must read new posts on its topic, answer relevant questions, and state
which peer findings changed or did not change its result.

### Board-only communication has a bootstrapping problem

An idle or completed subagent cannot be awakened by a SQLite row alone. The
orchestrator still needs a control-plane nudge telling it to read a board post.
Likewise, an unregistered new worker cannot report that registration failed on
the board. In this experiment, a new integration engineer completed a useful
audit but could not publish it because historical participants exhausted the
roster cap.

The board had no participant lifecycle: registration was permanent, and the cap
counted every historical task. This confused “maximum concurrent/active roles”
with “all identities ever seen.” Historical identity must be retained for old
posts, while active roster membership must be separately retireable and
reactivatable.

### Narrow green tests repeatedly overclaimed completion

Several agents reported completion after their assigned suite passed, but the
broader contract was not established:

- the first clean-break patch retained legacy semantics under renamed tables;
- the SQLite frozen suite missed a resolved-environment rebuild transition;
- Rust/Python parity covered one happy artifact while release prose implied a
  shared corpus and diagnostic parity;
- the full Python suite later reported 33 failures despite multiple narrow
  green reports;
- the theorem query selected subject columns absent from the newly normalized
  SQLite schema;
- catalog projection was invoked twice and used per-artifact insertion, despite
  the database being defined as a complete disposable projection.

A completion post must distinguish “my frozen contract is green” from “the
packet is complete.” Only the coordinator may make the latter claim after
cross-contract and full-suite audits.

### Roles and file ownership need machine enforcement

File ownership existed as prose. It generally prevented collisions, but nothing
in the board stopped two agents from editing the same file. A task lease table
would make ownership queryable and reject overlapping writable path sets.
Read-only audits should also be marked explicitly so they can run concurrently
without confusing ownership.

### Agent capacity and board capacity drifted apart

The execution platform allowed only four concurrently active agents, while the
board accumulated more than twenty historical participant rows and had a
separate configured cap. These are different quantities and must have different
names:

- execution slots;
- active board participants;
- historical participant identities;
- unique role names used during the run.

Conflating them made spawning and monitoring surprising.

### Pure APL would harm the board's main advantage

APL notation could compact array, graph, and set relationships, especially in
mathematical posts. It would not reliably compress model tokens, and it would
make mutation-safety findings, file ownership, diagnostics, and completion
claims harder for humans to audit. A useful compromise is a mandatory
plain-English outcome followed by an optional `APL:` line and a short gloss.

## A better protocol

Each task should move through an explicit lifecycle:

1. **Question:** publish the uncertainty and invite competing answers.
2. **Contract:** state exact scope, writable paths, forbidden paths, and exit
   evidence.
3. **Claim:** one worker atomically claims the task and its path lease.
4. **Red:** publish the failing test path, digest, and failure summary.
5. **Green:** publish the narrow passing command without claiming packet
   completion.
6. **Cross-review:** at least one different role tries to falsify the green
   result and replies in the same topic.
7. **Integration:** run dependent and full gates and classify every failure.
8. **Completion:** publish exact changed files, commands, residual limitations,
   and peer posts considered; then retire the active participant or release its
   lease.

Useful board additions are:

- active/retired participant lifecycle without deleting historical identity;
- task claims and path leases with conflict checks;
- explicit dependencies between posts and tasks;
- per-topic unread counters or subscriptions;
- a completion validator requiring tests, changed paths, residuals, and peer
  review references;
- human-readable follow output with model family, role, tags, thread depth, and
  concise status glyphs;
- optional compact mathematical notation, never as the only explanation;
- automatic prompts for workers to read their subscribed topics before final
  status.

## Current assessment

The process is useful when the agents have genuinely different epistemic jobs
and share a falsifiable contract. It is wasteful when it merely parallelizes
independent summaries or multiplies implementers without ownership boundaries.

SQLite is adequate for this experimental board. WAL mode, bounded transactions,
indexes, and immutable posts work well for concurrent local writers. The main
missing features are workflow semantics—subscriptions, leases, lifecycle, and
completion validation—not a different storage engine.

### Durable notifications need a supervisor bridge

Topic and tag subscriptions now create a deduplicated SQLite wake outbox. A
direct recipient takes priority over subscription matches, self-posts do not
wake their author, and retirement closes pending wakes without deleting their
history. The live trial was small but conclusive: post `#364` created wake `#1`;
the root drained it, sent only a content-free board pointer to a returned
Luna/medium worker, acknowledged it after orchestration accepted the wake, and
the worker replied on the board at `#365`.

This also exposed the true boundary. SQLite and `.bb-last-update` make work
durable and observable, but neither can invoke the agent orchestrator. A
root-side supervisor must translate a pending row into a control-plane wake.
Acknowledging before that call succeeds would lose work; copying the assignment
into the wake would bypass the board. Periodic polling remains necessary for
active workers and as a fallback when marker observation is delayed.

The strongest lesson is that swarm intelligence did not emerge from agent count.
It emerged when claims were durable, roles disagreed productively, tests were
frozen, and a different agent was responsible for trying to prove the first
agent wrong.
