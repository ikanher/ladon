# Ladon feedback after the assembled Adam energy theorem

The fresh compiled lineage is useful: it exposes the actual expected-energy
producer -> physical energy cap -> public output theorem chain. Summary,
declaration-rooted routes and bottlenecks all succeed on the installed CLI.
The fresh closure has 2,218 nodes and 59,621 edges with no recorded omissions.
The selected route has two proof-value edges. Its route and dominator populations
are truncated; that limitation stays visible and is not used as a closure proof.

The lineage refresh takes 38.8 seconds and peaks at about 9.15 GB sampled
aggregate process-tree RSS. Stored routes/bottlenecks take about 3.9 seconds and
roughly 66–68 MB. The successful lexical full rebuild takes 108.9 seconds and
about 118 MB. Thus these particular operations do not need a 48 GiB cap, but
Lean-backed refresh exceeds an 8 GiB budget; the existing larger budget is useful.

The main new friction is index update refusing to proceed with retained lineage
closures, forcing a whole lexical rebuild for a small Lean change. Preserving
old compiled evidence under its original generation while updating names would
help daily proof development. The mutation guard behaved correctly: root added
an audit during the first full build, Ladon rejected it, and a quiescent retry
succeeded. This execution mistake is not a Ladon defect.

A diagnostic wording issue deserves investigation: a max-nodes=3000 query
reports 3001 observed recursive rows and 666 returned distinct nodes, despite a
2,218-node summary. The result reports truncation correctly. Distinguishing
recursive-row and unique-node caps would make this easier to plan.

Prior R01 feedback still supplies source-goal completion and discovery tests:
the earlier same-file declaration context was lost, and a single le_trans
candidate produced conflicting evidence references. Those failures were not
retested here. No claim is made that all features have now been exercised.

See summary.json and raw results/receipts. Root Lean compilation, standard-axiom
policy and semantic self-audit are separate from these tool observations.
