"""Shared, fully validated inputs for offline result views."""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from ladon.result_assessments import validate_result_assessments
from ladon.result_inspection_cards import manifest_cards
from ladon.result_inspection_checks import checking_cards, project_checking_cards
from ladon.result_lineage import lineage_sections
from ladon.result_lineage_inputs import validate_lineage_inputs
from ladon.result_resolution import resolve_result_targets


@dataclass
class DossierInputs:
    """Owner projections and their complete cursor-binding observations."""

    catalog: dict
    resolved: list
    resolutions: dict
    sections: dict
    assessments: dict | None
    lineage: dict | None
    stored: dict


def prepare_dossier(manifest, artifacts, *, assessments=None, lineage_inputs=None,
                    lineage_base=Path('.'), target_ids=None, lineage_reference_base=None):
    """Resolve a validated manifest; validate all supplied checks and stores."""
    companion = validate_result_assessments(assessments, manifest) if assessments is not None else None
    lineage = validate_lineage_inputs(lineage_inputs, manifest) if lineage_inputs is not None else None
    catalog, resolved = resolve_result_targets(manifest, artifacts)
    resolutions = {row['targetId']: row for row in resolved}
    checks = checking_cards(manifest, catalog, resolutions, target_ids=target_ids)
    sections = manifest_cards(manifest, resolutions, companion)
    stored = lineage_sections(manifest, resolutions, lineage, lineage_base,
                              reference_base=lineage_reference_base)
    sections.update(checking=checks, **stored)
    return DossierInputs(catalog, resolved, resolutions, sections, companion, lineage, stored)


def project_dossier(inputs, manifest, target_ids):
    """Project selection-dependent checking rows from an owned validated snapshot."""
    checks = project_checking_cards(manifest, inputs.sections['checking'], target_ids)
    sections = dict(inputs.sections)
    sections['checking'] = checks
    return replace(inputs, sections=sections)
