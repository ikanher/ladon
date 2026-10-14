"""Scoped provider projections retain the exact observed local argument."""

from ladon.correspondence_interpretation import closed, text

DEFAULT_PROFILE = "declaration-scoped-application-v1"
SCOPED_PROFILE = "scoped-local-argument-v1"
TRANSPORT_PROFILE = "scoped-identity-transport-v2"
PROVIDER_KEYS = {"index", "status", "localId", "value", "closedType", "closedProof"}
PROVIDER_STATUSES = {"scoped-boundary", "scoped-local-value", "scoped-expression"}


def profile_is_scoped(proof_slice):
    profile = proof_slice["helper"]["profile"]
    if profile not in {DEFAULT_PROFILE, SCOPED_PROFILE, TRANSPORT_PROFILE}:
        raise ValueError("unsupported proof slice profile")
    return profile in {SCOPED_PROFILE, TRANSPORT_PROFILE}


def _validate_provider_order(application):
    expected = [arg["index"] for arg in application["arguments"] if arg["isProp"]]
    providers = application["providerObservations"]
    if (not isinstance(providers, list) or any(not isinstance(row, dict) for row in providers)
            or [row.get("index") for row in providers] != expected):
        raise ValueError("scoped providers must retain every ordered AND premise")
    return providers


def _validate_provider_row(row, locals_, expression_validator):
    closed(row, PROVIDER_KEYS, "scoped provider")
    if row["status"] not in PROVIDER_STATUSES:
        raise ValueError("unsupported scoped provider status")
    text(row["closedType"], "closed provider type")
    text(row["closedProof"], "closed provider proof")
    if row["value"] is not None:
        expression_validator(row["value"])
    if row["status"] == "scoped-expression":
        if row["localId"] is not None or row["value"] is not None:
            raise ValueError("expression provider cannot invent a local")
        return
    local = locals_.get(row["localId"])
    if local is None or not local["isProp"] or row["value"] != local["letValue"]:
        raise ValueError("provider disagrees with its scoped local")
    if (row["status"] == "scoped-boundary") != (row["value"] is None):
        raise ValueError("provider boundary/value classification changed")


def _validate_scope_observations(application, locals_):
    path = application["scopePath"]
    if not isinstance(path, list) or len(path) > 64 or any(
        type(index) is not int or not 0 <= index <= 4096 for index in path
    ):
        raise ValueError("invalid bounded lexical scope path")
    if not _valid_nested_ids(application["nestedLocalIds"], locals_):
        raise ValueError("nested scope identities must belong to the observed context")


def _valid_nested_ids(nested, locals_):
    return (isinstance(nested, list)
            and all(isinstance(identity, str) and identity in locals_ for identity in nested)
            and len(nested) == len(set(nested)))


def validate_provider_rows(application, expression_validator):
    providers = _validate_provider_order(application)
    locals_ = {row["localId"]: row for row in application["localContext"]}
    for row in providers:
        _validate_provider_row(row, locals_, expression_validator)
    _validate_scope_observations(application, locals_)


def premise_rows(application, *, scoped):
    providers = {row["index"]: row for row in application["providerObservations"]} if scoped else {}
    result = []
    for arg in application["arguments"]:
        if not arg["isProp"]:
            continue
        row = {"occurrence": arg["index"], "proposition": arg["type"],
               "provider": arg["expression"], "providerStatus": "observed-unexpanded"}
        if scoped:
            observed = providers[arg["index"]]
            row["providerStatus"] = observed["status"]
            row["providerObservation"] = {
                key: observed[key] for key in ("localId", "value", "closedType", "closedProof")
            }
        result.append(row)
    return result


def provider_frontiers(premises, *, scoped):
    return [{"reason": ("provider-boundary" if p["providerStatus"] == "scoped-boundary"
                        else "provider-unreplayed") if scoped else "provider-unexpanded",
             "occurrence": p["occurrence"]} for p in premises]
