from __future__ import annotations

from ladon.theorem_cli import build_theorem_parser


def test_lineage_parser_exposes_bounded_views_and_refresh_policy() -> None:
    parser = build_theorem_parser()
    args = parser.parse_args([
        "lineage", "Demo.target", "--view", "bottlenecks", "--from", "trust",
        "--edge-kind", "value", "--refresh", "never", "--max-depth", "3",
    ])
    assert args.theorem_command == "lineage"
    assert args.view == "bottlenecks"
    assert args.boundary == "trust"
    assert args.refresh == "never"
    assert args.max_depth == 3


def test_lineage_parser_accepts_repeated_roots_and_custom_index() -> None:
    parser = build_theorem_parser()
    args = parser.parse_args([
        "lineage", "Demo.target", "--root", "Demo", "--root", "Init",
        "--index", "/tmp/demo.sqlite",
    ])
    assert args.roots == ["Demo", "Init"]
    assert args.index == "/tmp/demo.sqlite"
