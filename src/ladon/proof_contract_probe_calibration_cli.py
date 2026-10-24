"""Ordinary CLI entry points for the explicitly finite calibration profile."""
from pathlib import Path

from .proof_contract_io import load_bounded_plans


def add_probe_calibration_parsers(subparsers):
    profile = subparsers.add_parser('probe-calibration-profile', help='Describe the finite separating-family calibration')
    profile.add_argument('--output', type=Path)
    probe = subparsers.add_parser('probe-calibration', help='Compare or check Fin 5 → Bool calibration objects')
    probe.add_argument('--input', type=Path, required=True)
    probe.add_argument('--output', type=Path)


def probe_calibration(args):
    from .proof_contract_probe_calibration import probe_calibration_profile, run_probe_calibration

    if args.operation == 'probe-calibration-profile':
        return probe_calibration_profile()
    return run_probe_calibration(load_bounded_plans([args.input], max_bytes=8 * 1024**2)[0])
