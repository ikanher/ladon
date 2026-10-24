"""Input shape and resource checks for backward templates."""
from datetime import UTC, datetime

_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_MAX_BRANCHES = 128
_MAX_OCCURRENCES = 256
_MAX_CHOICES = 4096
_MAX_REFS = 256
_MAX_ID_BYTES = 512
_INTERFACE_FIELDS = frozenset({"interfaceId", "endpointId", "operatorId", "objectId", "domainId", "representationId", "inputTypeId", "outputTypeId", "inputScaleId", "outputScaleId", "inputNormId", "outputNormId", "conclusionId", "evidenceRefs"})
_RULE_FIELDS = frozenset({"ruleId", "ruleRef", "ruleDeclaration", "profileDigest", "attributionStatus", "evidenceRefs"})

def _read_bounds(raw):
    bounds = _closed_mapping(raw, "bounds")
    allowed = {"maxBranches", "maxPremiseOccurrences", "maxOutputBytes", "deadlineUtc"}
    if set(bounds) - allowed:
        raise ValueError("unknown resource bound")
    caps = {
        "maxBranches": _bounded_integer(bounds, "maxBranches", _MAX_BRANCHES, 1),
        "maxPremiseOccurrences": _bounded_integer(
            bounds, "maxPremiseOccurrences", _MAX_OCCURRENCES, 1
        ),
        "maxOutputBytes": _bounded_integer(
            bounds, "maxOutputBytes", _MAX_OUTPUT_BYTES, 1024
        ),
    }
    return caps, _parse_deadline(bounds.get("deadlineUtc"))


def _bounded_integer(bounds, key, hard, minimum):
    value = bounds.get(key, hard)
    if type(value) is not int or not minimum <= value <= hard:
        raise ValueError(f"{key} must be an integer within supported limits")
    return value


def _parse_deadline(value):
    if value is None:
        return None
    if type(value) is not str or len(value) > _MAX_ID_BYTES or len(value.encode()) > _MAX_ID_BYTES:
        raise ValueError("deadlineUtc must be a bounded absolute timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("deadlineUtc must be an ISO timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError("deadlineUtc must include a timezone")
    return parsed.astimezone(UTC)

def _deadline_expired(deadline, observation=None):
    if observation is not None:
        return observation.expired()
    return deadline is not None and datetime.now(UTC) >= deadline


def _closed_mapping(value, label):
    if value is None:
        return {}
    if type(value) is not dict:
        raise TypeError(f"{label} must be an object")
    return value


def _identifier(value, label):
    if type(value) is not str or not value.strip() or len(value) > _MAX_ID_BYTES:
        raise ValueError(f"{label} must be a nonempty identifier of at most 512 bytes")
    if len(value.encode("utf-8")) > _MAX_ID_BYTES:
        raise ValueError(f"{label} must be a nonempty identifier of at most 512 bytes")


def _validate_rule_evidence(raw):
    if type(raw) is not dict or set(raw) != _RULE_FIELDS:
        raise ValueError("rule evidence has an invalid closed shape")
    for key in _RULE_FIELDS - {"evidenceRefs"}:
        _identifier(raw[key], "rule evidence " + key)
    _bounded_ref_list(raw["evidenceRefs"], "rule evidence evidenceRefs", nonempty=True)
    return raw


def _validate_interface(raw):
    if type(raw) is not dict or set(raw) != _INTERFACE_FIELDS:
        raise ValueError("endpoint interface has an invalid closed shape")
    for key in _INTERFACE_FIELDS - {"evidenceRefs"}:
        _identifier(raw[key], "interface " + key)
    if raw["operatorId"] != raw["objectId"]:
        raise ValueError("interface operatorId must equal objectId")
    _bounded_ref_list(raw["evidenceRefs"], "interface evidenceRefs", nonempty=True)
    return raw


def _validate_interfaces(raw, maximum):
    if type(raw) not in (list, tuple) or len(raw) > maximum:
        raise ValueError("premise occurrence count exceeds its preflight cap")
    return [_validate_interface(row) for row in raw]


def _bounded_ref_list(value, label, nonempty=False):
    if type(value) is not list or len(value) > _MAX_REFS or (nonempty and not value):
        raise ValueError(f"{label} must be a bounded nonempty reference list")
    for row in value:
        _identifier(row, label + " item")


def _count_refs(raw):
    total = 0
    def visit(value):
        nonlocal total
        if isinstance(value, dict):
            for key, child in value.items():
                if key.endswith("Refs") and type(child) is list:
                    total += len(child)
                visit(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                visit(child)
    visit(raw)
    return total

