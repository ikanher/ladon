# Premise-provenance family baseline review

**Reviewed:** 2026-11-12  
**Registration:** `pitfall-common-registration-v3`  
**Registration SHA-256:** `52f5acda607d5a56230db7617796211ab74a9ecbf15ff6af0eec75195dda78f0`  
**Disposition:** Accepted as the qualified four-case family batch.

The independent reviewer checked `run-summary.json`, each case's command,
host and workspace receipts, all proof-slice outputs, the live isolation
report, and the accepted corpus/rubrics. The command, source/declaration and
selector bindings match v3. Workspace hashes and source/artifact identities
match the accepted corpus, and every run binds the preserved runtime identity
and registration hash.

All four isolation checks passed. Each selected case imported successfully;
all 23 excluded corpus modules were unavailable through either an exact
missing-module diagnostic or, for the absent Mathlib package, its exact
missing-namespace-prefix diagnostic. The sibling artifact injection imported
successfully and was then rejected by the allowlist guard. The unrelated
compiler failure was not accepted as isolation evidence. Workspaces were
restored to their frozen allowlists after the checks.

Cases 01, 02 and 04 produced complete proof slices. Case 01 exposes
`HasConclusion.proof` applied to the implicit `h : HasConclusion P`, which
supports its registered source/formal mismatch judgment. Case 02 exposes the
same projection from an explicit provider and is a justified control. Case 04
exposes the projection through its arithmetic provider; the accepted source
defines that provider from `arithmeticFact := by decide`, so it is a justified
control. These routes do not establish that a premise is mathematically
necessary.

Case 03 matches the post-freeze v3 negative capability-probe contract. It
qualifies only the exact local-binder selector limitation. It remains
unsupported and unscored for detection/control purposes; it does not establish
that the provider route is absent.

All cases were within the 600-second limit. Preparation-inclusive measurements
were 27.289 s, 27.124 s, 22.822 s, and 28.037 s; peak RSS was 1,673,093,120 B,
1,673,977,856 B, 1,667,964,928 B, and 1,671,897,088 B respectively. The
premise-provenance family batch is accepted; no operation-definedness family
batch has run, and this does not establish Navier–Stokes exposition detection.
