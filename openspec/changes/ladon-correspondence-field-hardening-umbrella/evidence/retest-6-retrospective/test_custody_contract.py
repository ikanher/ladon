"""Reject altered retrospective mappings while preserving frozen sources."""

import json
from pathlib import Path
import shutil

import pytest

from verify import verify


@pytest.mark.parametrize("mutation", ["source", "selection", "evidence", "absence"])
def test_changed_mapping_rejected(tmp_path, mutation):
    base = Path(__file__).resolve().parent
    for name in ("source-manifest.json", "cases.json", "inverse-source.txt", "pressure-source.txt"):
        shutil.copyfile(base / name, tmp_path / name)
    path = tmp_path / "cases.json"
    corpus = json.loads(path.read_text())
    cases = corpus["cases"]
    if mutation == "source":
        cases[-1]["sourceBinding"]["startLine"] = 3533
    elif mutation == "selection":
        cases[-1]["selection"]["declaration"] = "Wrong.declaration"
    elif mutation == "evidence":
        cases[0]["observedEvidenceQuote"] = "An invented first-assessment sentence."
    else:
        cases[0]["expected"]["exactNativeBridge"] = "absent"
    path.write_text(json.dumps(corpus))
    with pytest.raises(AssertionError):
        verify(tmp_path)
