"""Immutable attributed observations; source custody does not establish mathematics."""

import copy
import json
from pathlib import Path

from ladon.correspondence_interpretation import closed, text
from ladon.investigation import MAX_RECORDS, SourceReader
from ladon.proof_slice import digest

RECORD_KEYS = {"schema", "id", "source", "author", "assertion", "comparison", "evidence",
               "formalSources", "dependencies"}
RECORD_V2_KEYS = RECORD_KEYS | {"contractAnalysis"}
ENTRY_KEYS = {"observationId", "record", "responses", "reconciliations"}


def _validate_record_shape(record):
    if not isinstance(record, dict):
        raise TypeError("observation record must be an object")
    version = record.get("schema")
    if version == "ladon-investigation-observation-v1":
        closed(record, RECORD_KEYS, "observation record")
    elif version == "ladon-investigation-observation-v2":
        closed(record, RECORD_V2_KEYS, "observation record")
        from ladon._investigation_contract_observations import validate_contract_analysis

        validate_contract_analysis(record["contractAnalysis"], record.get("id"))
    else:
        raise ValueError("unsupported observation schema")
    return version == "ladon-investigation-observation-v2"


def _record(record, reader, scope):
    _validate_record_shape(record)
    for key in ("id", "author", "assertion", "comparison", "evidence", "dependencies"):
        text(record[key], "observation " + key)
    source = record["source"]
    closed(source, {"path", "sha256", "startLine", "endLine", "quote"}, "observation source")
    reader.span(source, "quote")
    if (source["path"] != scope["path"] or source["sha256"] != scope["sha256"]
            or not scope["startLine"] <= source["startLine"] <= source["endLine"] <= scope["endLine"]):
        raise ValueError("observation source is outside investigation scope")
    formal = record["formalSources"]
    if not isinstance(formal, list) or len(formal) > 64:
        raise ValueError("invalid bounded observation formal sources")
    for row in formal:
        closed(row, {"path", "sha256", "startLine", "endLine", "statement"}, "formal source")
        reader.span(row, "statement")


def observation_packet(entry):
    record = entry["record"]
    contract = record.get("schema") == "ladon-investigation-observation-v2"
    packet = {"schema": ("ladon-investigation-observation-challenge-v2" if contract
                          else "ladon-investigation-observation-challenge-v1"),
              "subject": entry["observationId"], "source": copy.deepcopy(record["source"]),
              "sourceQuote": record["source"]["quote"], "assertion": record["assertion"],
              "formalSources": copy.deepcopy(record["formalSources"]),
              "dependencies": record["dependencies"],
              "authority": ("The bounded native attachment was structurally validated; source interpretation remains attributed."
                            if contract else "Compare the source and argument; no native proof is supplied.")}
    if contract:
        packet["contractAnalysis"] = copy.deepcopy(record["contractAnalysis"])
    packet["challengeDigest"] = digest(packet)
    return packet


def observation_responses(entry):
    from ladon.investigation_correspondence import _apply_reconciliations, _validate_first_responses

    packet = observation_packet(entry)
    packets = {entry["observationId"]: packet}
    firsts = _validate_first_responses(entry["responses"], packets)
    effective = _apply_reconciliations(entry["reconciliations"], firsts, packets)
    if any(r["reviewer"] == entry["record"]["author"] for r in effective.values()):
        raise ValueError("observation review requires a distinct attributed reviewer")
    return list(effective.values())


def validated_observations(plan, root):
    rows = plan.get("observations", [])
    if not isinstance(rows, list) or len(rows) > MAX_RECORDS:
        raise ValueError("invalid bounded observations")
    limit = (32 if plan["version"] == 3 else 4) * 1024**2
    if len(json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode()) > limit:
        raise ValueError("observation plan exceeds byte bound")
    reader = SourceReader(Path(root))
    reader.span(plan["scope"])
    identities, names = set(), set()
    for entry in rows:
        _validate_entry(entry, reader, plan["scope"], identities, names)
    return rows


def _validate_entry(entry, reader, scope, identities, names):
    closed(entry, ENTRY_KEYS, "stored observation")
    _record(entry["record"], reader, scope)
    identity, name = digest(entry["record"]), entry["record"]["id"]
    if entry["observationId"] != identity or identity in identities or name in names:
        raise ValueError("altered or duplicate observation identity")
    identities.add(identity)
    names.add(name)
    for key in ("responses", "reconciliations"):
        if not isinstance(entry[key], list) or len(entry[key]) > MAX_RECORDS:
            raise ValueError("invalid bounded observation " + key)
    observation_responses(entry)


def inspect_observations(plan, root):
    from ladon.investigation import assess

    assess(plan, Path(root))
    return copy.deepcopy(validated_observations(plan, root))


def record_observation(plan, record, root):
    from ladon.investigation import assess

    assess(plan, Path(root))
    owned = copy.deepcopy(plan)
    entry = {"observationId": digest(record), "record": copy.deepcopy(record),
             "responses": [], "reconciliations": []}
    owned.setdefault("observations", []).append(entry)
    validated_observations(owned, root)
    return owned


def _observation(plan, subject, root):
    matches = [entry for entry in validated_observations(plan, root)
               if entry["observationId"] == subject]
    if len(matches) != 1:
        raise ValueError("unknown observation subject")
    return matches[0]


def challenge_observation(plan, subject, root):
    from ladon.investigation import assess

    assess(plan, Path(root))
    return observation_packet(_observation(plan, subject, root))


def ingest_observation_response(plan, packet, response, root, first=None):
    from ladon.investigation_correspondence import validate_response

    expected = challenge_observation(plan, response.get("subject"), root)
    if packet != expected:
        raise ValueError("altered observation challenge binding")
    validate_response(response, expected)
    owned = copy.deepcopy(plan)
    entry = _observation(owned, response["subject"], root)
    stored = {"responseId": digest(response), **copy.deepcopy(response)}
    if first is not None:
        stored["firstResponseId"] = first
    entry["responses" if first is None else "reconciliations"].append(stored)
    validated_observations(owned, root)
    return owned


def review_relation(responses, key, unresolved="unresolved"):
    values = {r[key] for r in responses}
    if len(values) > 1:
        return "conflicted"
    return next(iter(values)) if values else unresolved


def observation_finding(entry):
    responses = observation_responses(entry)
    record = entry["record"]
    finding = {"kind": "observation", "findingId": entry["observationId"],
            "source": copy.deepcopy(record["source"]), "assertion": record["assertion"],
            "comparison": record["comparison"],
            "statementRelation": review_relation(responses, "classification"),
            "methodRelation": review_relation(responses, "method"),
            "sourceFidelity": review_relation(responses, "sourceFidelity"),
            "formalSupport": "not-established", "mathematicalFalsity": "not-established",
            "evidence": record["evidence"], "dependencies": record["dependencies"],
            "attribution": record["author"], "responses": copy.deepcopy(entry["responses"]),
            "reconciliations": copy.deepcopy(entry["reconciliations"]),
            "effectiveResponses": copy.deepcopy(responses)}
    if record.get("schema") == "ladon-investigation-observation-v2":
        from ladon._investigation_contract_observations import project_contract_finding

        finding = project_contract_finding(finding, record, responses)
    return finding


def observation_work(entry):
    finding = observation_finding(entry)
    resolved = (finding["statementRelation"] in {"aligned", "mismatch"}
                and finding["methodRelation"] in {"same", "different"}
                and finding["sourceFidelity"] == "faithful")
    if resolved:
        return None
    return {"kind": "independent-observation-review", "subject": entry["observationId"],
            "source": copy.deepcopy(entry["record"]["source"])}


def add_observation_status(result, plan, root):
    entries = validated_observations(plan, root)
    result["findings"].extend(observation_finding(entry) for entry in entries)
    work = [item for entry in entries if (item := observation_work(entry)) is not None]
    result["next"].extend(work)
    result["counts"].update(observations=len(entries), pendingObservations=len(work),
                            actionable=len(result["next"]))
    result["coverage"].update(reviewedObservations=len(entries) - len(work))
    if any(entry["record"]["schema"] == "ladon-investigation-observation-v2" for entry in entries):
        result["authority"] += "; bounded native attachment shape and references validated, without checker or Lean replay"
        result["nonclaims"] = [claim for claim in result["nonclaims"]
                              if "no lean, network, model service or automatic semantic comparison was run"
                              not in claim.lower()]
        result["nonclaims"].append(
            "Native attachment validation is bounded; it does not link the graph to source interpretation or establish theorem truth or source completeness."
        )
    if work and result["remainingSeconds"] > 0:
        result.update(status="continue", mayFinalize=False)
