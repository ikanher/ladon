from __future__ import annotations

import json

from ladon.entrypoint import main


def test_version_command_reports_machine_readable_package_and_source(capsys) -> None:
    assert main(["version", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "ladon-version-result-v1"
    assert payload["package"]["version"]
    assert payload["package"]["distributionIdentity"].startswith("sha256:")
    if payload["source"]["status"] == "observed":
        assert isinstance(payload["source"]["dirty"], bool)


def test_standard_version_flag_is_supported(capsys) -> None:
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.startswith("ladon ")
