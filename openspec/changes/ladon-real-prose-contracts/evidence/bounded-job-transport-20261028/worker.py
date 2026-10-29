"""Qualification worker: exact decode/re-encode, no connection/admission."""
import sys
from ladon.bounded_json_transport import TransportLimits, pack_json, unpack_json

limits = TransportLimits()
wire = sys.stdin.buffer.read(limits.max_wire_bytes+1)
value = unpack_json(wire, limits=limits)
sys.stdout.buffer.write(pack_json(value, limits=limits))
