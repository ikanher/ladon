"""Fresh baseline for the copied, source-identical generic public matrix."""
import json
import sys
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

repo = Path.cwd()
base = Path(__file__).resolve().parent
root = Path((base / "qualified-set/ROOT.txt").read_text().strip())
mode = sys.argv[1]
sys.path.insert(0, str(repo / "tests"))
from real_prose_connection_live_helpers import authored_input, formal_input

q = base / "qualified-set"
if mode == "formal":
    value = formal_input(root)
    (q / "FORMAL.json").write_text(json.dumps(value, ensure_ascii=False))
    print({"mode": mode, "status": value["status"], "snapshotId": value["snapshotId"]}, flush=True)
elif mode == "authored":
    value = authored_input(root, global_scope=False)
    (q / "AUTHORED.json").write_text(json.dumps(value, ensure_ascii=False))
    print({"mode": mode, "status": value["status"], "snapshotId": value["snapshotId"]}, flush=True)
elif mode == "connection":
    from ladon.proof_contract_cli import contract_main
    request = q / "bootstrap-request.json"
    request.write_text(json.dumps({"schema": "ladon-real-prose-connection-request-v1",
        "term": "by intro original; exact original", "premises": []}))
    output = q / "CONNECTION.json"
    buffer = StringIO()
    with redirect_stdout(buffer):
        code = contract_main(["connect-real-prose-bound", "--formal", str(q/"FORMAL.json"),
            "--authored", str(q/"AUTHORED.json"), "--formal-root", str(root),
            "--prose-root", str(root), "--request", str(request), "--timeout-seconds", "300",
            "--output", str(output)])
    value = json.loads(output.read_text() if output.exists() else buffer.getvalue())
    print({"mode": mode, "exitCode": code, "status": value.get("status"),
           "snapshotId": value.get("snapshotId")}, flush=True)
    assert code == 0 and value["status"] == "connected"
else:
    raise ValueError("unknown prep mode")
