"""Reproduce the overlapping source root failure with an installed Ladon CLI."""

import argparse
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ladon", default="ladon", help="Path to the Ladon executable")
    args = parser.parse_args()
    fixture = Path(__file__).resolve().with_name("repro")
    with TemporaryDirectory(prefix="ladon-overlap-repro-") as directory:
        index = Path(directory) / "index.sqlite"
        result = subprocess.run(
            [args.ladon, "proof-search", "index", "build", "--repo-root", str(fixture),
             "--index", str(index), "--format", "json", "--progress"],
            check=False,
        )
        print(f"Ladon exit code: {result.returncode}", flush=True)
        print(f"Index published: {index.is_file()}", flush=True)
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
