from __future__ import annotations

from pathlib import Path


def test_release_docs_and_skill_name_all_public_proof_search_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    docs = Path("docs/CLI.md").read_text(encoding="utf-8")
    skill = Path("../codex-skills/ladon/SKILL.md").read_text(encoding="utf-8")
    for command in ("search name", "search type", "explain", "consumers", "constructor"):
        assert command in readme
        assert command in docs or command in skill
