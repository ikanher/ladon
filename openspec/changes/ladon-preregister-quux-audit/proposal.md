# Ladon Preregister Quux Audit

## Why

Before running the refreshed Ladon analyzer on Quux, record expected signals so
the run is an actual validation exercise instead of post-hoc interpretation.

This is not fully blind: earlier smoke runs have already exercised parts of
Quux. The useful discipline is that this packet records predictions before the
fresh validation run and distinguishes repo-inspection expectations from
observed output.

## What

- Pre-register expected Ladon findings for `/home/codex/projects/quux`.
- Run a project-level text DAG audit and an owner-level Lean-backed audit.
- Compare observed signals against the pre-registration.

## Non-Goals

- No Quux source changes.
- No claim that every Ladon finding is a defect.
- No whole-repo dead-code claim.
