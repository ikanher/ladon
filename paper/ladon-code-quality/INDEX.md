# Ladon Code Quality Literature Review

This directory is a local seed corpus for Ladon's code-quality and proof-code
analysis work. ArXiv e-print source tarballs are preferred whenever available.
When arXiv only returned a PDF, or when the work is a foundational non-arXiv
paper, the artifact is stored under `pdf/` and marked as a fallback in
`manifest.json`.

## Layout

- `manifest.json`: machine-readable bibliography and artifact metadata.
- `arxiv/`: arXiv e-print source tarballs.
- `pdf/`: arXiv PDF fallbacks and non-arXiv foundational PDFs.
- `notes/`: reserved for follow-up reading notes.

## Reading Order For Ladon

1. **Graph and architecture core**

   Read McCabe (1976), Yamaguchi et al. (2014), Garcia et al. (2015), and
   Savidis/Savaki (2022). These justify Ladon's current graph-first direction:
   module DAGs, direct-import closure attribution, and future graph/atlas views.

2. **Queryable atlas and graph-database layer**

   Read Angles et al. (2016), Francis et al. (2018), and Haratian et al.
   (2024). These justify moving from static atlas JSON to queryable graph/index
   surfaces. The immediate Ladon implication is a small SQLite/property-graph
   export with canned queries before any UI.

3. **Architecture evolution and atlas diff**

   Read Musco/Monperrus/Preux (2014), Li et al. (2021), and
   Sas/Avgeriou/Uyumaz (2022). These support tracking dependency and smell
   evolution over time. The immediate Ladon implication is an atlas-diff packet:
   compare report graphs before/after a proof refactor or packet.

4. **Metric and smell calibration**

   Read Jin et al. (2023), Esposito et al. (2024), Han et al. (2022), and
   Zakeri-Nasrabadi et al. (2023). These are useful for making Ladon findings
   less arbitrary: thresholds should be calibrated and findings should be
   validated against review outcomes where possible.

5. **Similarity and repeated proof families**

   Read Zakeri-Nasrabadi et al. (2023) on source-code similarity and Dou et al.
   (2023) on LLM clone detection. These inform Ladon's declaration-family
   grouping and future proof-skeleton similarity work.

6. **Analyzer precision and benchmark realism**

   Read Hermann et al. (2026) and SQuaD (2025). These are cautionary sources:
   analyzer outputs need clear false-positive boundaries, datasets, and
   benchmark expectations.

7. **Proof-engineering context**

   Read Chen et al. (2018), PACT (2021), ProofNet (2023), LeanDojo (2023),
   Zhang/Ringer/First (2023), APOLLO (2025), Goedel-Prover (2025), ProofGym
   (2025), and APRIL (2026). These are not direct code-smell sources, but they
   inform Ladon's proof-code domain: proof context retrieval, compiler-feedback
   loops, benchmark/task boundaries, and LLM-assisted proof tooling.

## Local Corpus

### Metrics, Maintainability, And Smells

- `arxiv/2307.12082-software-code-quality-measurement.tar`
  - Software Code Quality Measurement: Implications from Metric Distributions.
  - Relevance: metric distributions and threshold design.

- `arxiv/2406.17354-architectural-smells-static-analysis-warnings.tar`
  - On the correlation between Architectural Smells and Static Analysis Warnings.
  - Relevance: combines architecture-level smells with local static warnings.

- `pdf/2306.01377-code-smell-datasets-validation-slr.pdf`
  - A systematic literature review on the code smells datasets and validation mechanisms.
  - Relevance: validation expectations for Ladon smell/finding classes.

- `arxiv/2205.07535-code-smells-modern-code-review.tar`
  - Code Smells Detection via Modern Code Review.
  - Relevance: links automated smells to human review workflows.

### Similarity, Clone Detection, And Repeated Proof Shapes

- `pdf/2306.16171-source-code-similarity-clone-detection-slr.pdf`
  - A systematic literature review on source code similarity measurement and clone detection.
  - Relevance: background for declaration-family and proof-skeleton comparison.

- `arxiv/2308.01191-llm-code-clone-detection-survey.tar`
  - Towards Understanding the Capability of Large Language Models on Code Clone Detection.
  - Relevance: separates deterministic clone signals from future LLM-assisted review.

- `arxiv/2012.08842-code-smell-detection-visualization-slr.tar`
  - Code smells detection and visualization: A systematic literature review.
  - Relevance: grouped atlas/reviewer views rather than raw metric lists.

### Program Graphs, Static Analysis, And Architecture Recovery

- `pdf/mccabe-1976-a-complexity-measure.pdf`
  - A Complexity Measure.
  - Relevance: graph-theoretic complexity foundation behind cyclomatic checks.

- `pdf/yamaguchi-2014-code-property-graphs.pdf`
  - Modeling and Discovering Vulnerabilities with Code Property Graphs.
  - Relevance: graph-unification pattern for syntax/control/dependency analysis.

- `arxiv/2507.16585-llmxcpg-code-property-graph-vulnerability.tar`
  - LLMxCPG.
  - Relevance: modern graph-guided LLM analysis direction.

- `arxiv/2602.18270-static-code-analyzers-security-survey.tar`
  - Many Tools, Few Exploitable Vulnerabilities.
  - Relevance: analyzer false-positive and benchmark caution.

- `pdf/garcia-2015-comparing-software-architecture-recovery.pdf`
  - Comparing Software Architecture Recovery Techniques Using Accurate Dependencies.
  - Relevance: architecture recovery and dependency accuracy.

- `pdf/moin-2022-software-architecture-mining-source-code.pdf`
  - Software Architecture Mining from Source Code with Dependency Graph Clustering and Visualization.
  - Relevance: future graph clustering and visual atlas work.

- `arxiv/1610.06264-foundations-of-modern-query-languages-for-graph-databases.tar`
  - Foundations of Modern Query Languages for Graph Databases.
  - Relevance: query foundations for a future Ladon atlas query engine.

- `arxiv/1802.09984-cypher-formal-semantics.tar`
  - Formal Semantics of the Language Cypher.
  - Relevance: property-graph query semantics for deciding how far Ladon should
    go beyond SQLite/canned queries.

- `arxiv/2407.02620-refexpo-reference-graph-extraction.tar`
  - RefExpo: Unveiling Software Project Structures through Advanced Dependency Graph Extraction.
  - Relevance: dependency graph extraction and project-structure recovery.

### Architecture Evolution And Atlas Diff

- `arxiv/1410.7921-software-dependency-graph-evolution.tar`
  - A Generative Model of Software Dependency Graphs to Better Understand Software Evolution.
  - Relevance: dependency graphs as evolving objects, directly informing atlas diff.

- `arxiv/2112.10934-software-architecture-erosion-survey.tar`
  - Understanding Software Architecture Erosion: A Systematic Mapping Study.
  - Relevance: atlas diff as architecture drift/erosion evidence.

- `arxiv/2203.08702-evolution-of-architectural-smells.tar`
  - On the evolution and impact of Architectural Smells.
  - Relevance: finding trajectories over time are more useful than one static smell snapshot.

### Datasets And LLM Evaluation

- `arxiv/2511.11265-squad-software-quality-dataset.tar`
  - SQuaD: The Software Quality Dataset.
  - Relevance: possible benchmark framing for Ladon finding calibration.

- `arxiv/2408.07082-llm-code-quality-evaluation.tar`
  - Evaluating Source Code Quality with Large Language Models.
  - Relevance: future LLM explanation layer, not core deterministic analysis.

### Proof Engineering And Theorem-Prover Tooling

- `arxiv/1810.11979-formal-proofs-tarjan-why3-coq-isabelle.tar`
  - Formal Proofs of Tarjan's Algorithm in Why3, Coq, and Isabelle.
  - Relevance: cross-system proof engineering comparison.

- `arxiv/2305.04369-getting-more-out-of-llms-for-proofs.tar`
  - Getting More out of Large Language Models for Proofs.
  - Relevance: LLM-assisted proof work with proof-checker boundaries.

- `arxiv/2102.06203-pact-proof-artifact-co-training.tar`
  - Proof Artifact Co-training for Theorem Proving with Language Models.
  - Relevance: proof artifacts and generated evidence should remain aligned.

- `arxiv/2302.12433-proofnet-autoformalizing-undergraduate-math.tar`
  - ProofNet: Autoformalizing and Formally Proving Undergraduate-Level Mathematics.
  - Relevance: finite task boundaries and benchmark framing for proof review.

- `arxiv/2306.15626-leandojo-retrieval-augmented-theorem-proving.tar`
  - LeanDojo: Theorem Proving with Retrieval-Augmented Language Models.
  - Relevance: premise/context retrieval strongly supports Ladon atlas queries
    over Lean declaration neighborhoods.

- `arxiv/2505.05758-apollo-llm-lean-collaboration.tar`
  - APOLLO: Automated LLM and Lean Collaboration for Advanced Formal Reasoning.
  - Relevance: human/LLM/Lean collaboration loops and reviewer-card framing.

- `arxiv/2502.07640-goedel-prover-open-source-automated-theorem-proving.tar`
  - Goedel-Prover.
  - Relevance: Lean formal proof generation context.

- `arxiv/2602.02990-april-lean-proof-repair-feedback.tar`
  - Learning to Repair Lean Proofs from Compiler Feedback.
  - Relevance: compiler/report feedback as structured proof-maintenance evidence.

- `pdf/proofgym-unifying-llm-based-theorem-proving.pdf`
  - PROOFGYM.
  - Relevance: common API and logging ideas for multi-prover tooling.

## Immediate Ladon Design Implications

- Keep deterministic graph extraction as the core. LLMs can explain or cluster
  later, but findings should remain reproducible.
- Make the atlas queryable before making it visual. Graph-query literature
  supports a small query surface over stable graph data; SQLite plus canned
  queries is the pragmatic next step.
- Add atlas diff before broadening smells. Architecture-evolution literature
  argues that finding trajectories and dependency drift are more useful than a
  single static smell snapshot.
- Treat findings as review triage, not proof of badness. The static-analysis
  literature repeatedly warns about false positives and validation gaps.
- Prefer calibrated class summaries over single hard-coded alarms. Ladon's
  unresolved-reference class counts and declaration-family groups are aligned
  with this direction.
- Use proof-context retrieval as the model for Lean review cards. LeanDojo and
  related proof-tooling papers suggest that useful proof assistance starts from
  accessible premises, local neighborhoods, and compiler/proof feedback, not
  from ungrounded summaries.
- Add future modules in this order: SQLite atlas export with canned queries,
  atlas diff, reviewer cards, then graph clustering/visualization.
