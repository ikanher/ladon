"""Stable public facade for Ladon's large-inventory contract.

The gate deliberately treats JSON and text as separate ordinary CLI runs. Each
representation gets an independent cold cache and reuses only that cache for
its paired warm run. Cohesive execution, normalization, result evaluation, and
data contracts live in neighboring modules; this facade preserves the existing
``ladon.large_inventory_gate`` import surface.
"""

from __future__ import annotations

from ladon.large_inventory_execution import (
    analysis_command,
    run_large_inventory_measurements,
)
from ladon.large_inventory_models import (
    ANALYSIS_COMMAND_TEMPLATE,
    LARGE_INVENTORY_GATE_SCHEMA,
    REQUIRED_SAMPLE_COUNT,
    LargeInventoryGateError,
    ScaleCeilings,
)
from ladon.large_inventory_normalization import (
    normalized_report_bytes,
    progress_cache_evidence,
    progress_phase_evidence,
)
from ladon.large_inventory_results import (
    available_cpu_count,
    reference_job_identity,
)


__all__ = [
    "LARGE_INVENTORY_GATE_SCHEMA",
    "ANALYSIS_COMMAND_TEMPLATE",
    "LargeInventoryGateError",
    "REQUIRED_SAMPLE_COUNT",
    "ScaleCeilings",
    "analysis_command",
    "available_cpu_count",
    "normalized_report_bytes",
    "progress_cache_evidence",
    "progress_phase_evidence",
    "reference_job_identity",
    "run_large_inventory_measurements",
]
