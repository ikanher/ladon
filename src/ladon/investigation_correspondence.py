"""Opt-in source-bound review with immutable first responses and native subjects."""

import copy
import json
from pathlib import Path

from ladon.correspondence_interpretation import closed, text
from ladon.investigation import SourceReader, initialize
from ladon.investigation_correspondence_inputs import sanitized_inputs, validate_bundle
from ladon.proof_slice import digest

PLAN_KEYS = {"version", "startedAt", "budgetSeconds", "scope", "units", "claims",
             "correspondenceBundles", "responses", "reconciliations"}
RESPONSE_KEYS = {"reviewer", "subject", "challengeDigest", "classification", "method",
                 "sourceFidelity", "evidence"}


def _bounded(plan):
    optional = {key for key in ("workBlockers", "observations") if key in plan}
    closed(plan, PLAN_KEYS | optional,
           "version-three investigation")
    if type(plan["version"]) is not int or plan["version"] != 3:
        raise ValueError("unsupported structured investigation version")
    for key in ("correspondenceBundles", "responses", "reconciliations"):
        if not isinstance(plan[key], list) or len(plan[key]) > 4096:
            raise ValueError("invalid bounded " + key)
    if len(json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode()) > 32 * 1024**2:
        raise ValueError("structured investigation exceeds 32 MiB")


def initialize_v3(source, root, *, minutes=90, unit_lines=80, now=None):
    plan = initialize(source, root, minutes=minutes, unit_lines=unit_lines, now=now)
    plan.update(version=3, correspondenceBundles=[], responses=[], reconciliations=[])
    return plan


def validated_entries(plan, root):
    _bounded(plan)
    SourceReader(Path(root)).span(plan["scope"])
    entries, subjects = [], set()
    for entry in plan["correspondenceBundles"]:
        closed(entry, {"kind", "subject", "bundle"}, "attached subject")
        actual = validate_bundle(entry["bundle"], root, plan["scope"])
        if entry != actual or entry["subject"] in subjects:
            raise ValueError("altered or duplicate attached subject")
        subjects.add(entry["subject"])
        entries.append(actual)
    return entries


def attach_bundle(plan, bundle, root):
    entries = validated_entries(plan, root)
    entry = validate_bundle(bundle, root, plan["scope"])
    if entry["subject"] in {row["subject"] for row in entries}:
        raise ValueError("duplicate attached subject; preserve first bundle")
    owned = copy.deepcopy(plan)
    owned["correspondenceBundles"].append(entry)
    _bounded(owned)
    return owned


def packet_for_entry(entry):
    inputs = sanitized_inputs(entry)
    packet = {"schema": "ladon-investigation-challenge-v3", "subject": entry["subject"],
              "sourceQuote": inputs["interpretation"]["source"]["quote"], **copy.deepcopy(inputs)}
    packet["challengeDigest"] = digest(packet)
    return packet


def challenge_packet_v3(plan, subject, root):
    matches = [entry for entry in validated_entries(plan, root) if entry["subject"] == subject]
    if len(matches) != 1:
        raise ValueError("unknown challenge subject")
    return packet_for_entry(matches[0])


def validate_response(response, packet):
    closed(response, RESPONSE_KEYS, "independent attributed response")
    for key in ("reviewer", "subject", "challengeDigest", "evidence"):
        text(response[key], "response " + key)
    enums = {"classification": {"aligned", "mismatch", "unresolved"},
             "method": {"same", "different", "unresolved"},
             "sourceFidelity": {"faithful", "ambiguous", "unresolved"}}
    if any(response[key] not in allowed for key, allowed in enums.items()):
        raise ValueError("unsupported attributed response classification")
    if (response["subject"] != packet["subject"]
            or response["challengeDigest"] != packet["challengeDigest"]):
        raise ValueError("response challenge binding changed")


def _validate_first_responses(stored_rows, packets):
    firsts, seen = {}, set()
    for stored in stored_rows:
        closed(stored, RESPONSE_KEYS | {"responseId"}, "first response")
        response = {key: stored[key] for key in RESPONSE_KEYS}
        identity = digest(response)
        if stored["responseId"] != identity or identity in firsts:
            raise ValueError("altered response identity")
        packet = packets.get(response["subject"])
        if packet is None:
            raise ValueError("response subject unavailable")
        validate_response(response, packet)
        owner = (response["subject"], response["challengeDigest"], response["reviewer"])
        if owner in seen:
            raise ValueError("duplicate reviewer first response")
        seen.add(owner)
        firsts[identity] = stored
    return firsts


def _apply_reconciliations(stored_rows, firsts, packets):
    effective, corrected = dict(firsts), set()
    for stored in stored_rows:
        closed(stored, RESPONSE_KEYS | {"responseId", "firstResponseId"}, "reconciliation")
        first = firsts.get(stored["firstResponseId"])
        if first is None or stored["firstResponseId"] in corrected:
            raise ValueError("unknown or duplicate reconciliation first response")
        response = {key: stored[key] for key in RESPONSE_KEYS}
        if (stored["responseId"] != digest(response) or response["subject"] != first["subject"]
                or response["challengeDigest"] != first["challengeDigest"]):
            raise ValueError("altered response identity or reconciliation binding")
        if response["reviewer"] != first["reviewer"]:
            raise ValueError("reconciliation reviewer attribution changed")
        validate_response(response, packets[response["subject"]])
        corrected.add(stored["firstResponseId"])
        effective[stored["firstResponseId"]] = stored
    return effective


def effective_responses(plan, entries):
    packets = {entry["subject"]: packet_for_entry(entry) for entry in entries}
    firsts = _validate_first_responses(plan["responses"], packets)
    effective = _apply_reconciliations(plan["reconciliations"], firsts, packets)
    return list(effective.values())


def ingest_response(plan, packet, response, root, first=None):
    entries = validated_entries(plan, root)
    effective_responses(plan, entries)
    expected = challenge_packet_v3(plan, response.get("subject"), root)
    if packet != expected:
        raise ValueError("altered challenge binding")
    validate_response(response, expected)
    owned = copy.deepcopy(plan)
    stored = {"responseId": digest(response), **copy.deepcopy(response)}
    if first is not None:
        stored["firstResponseId"] = first
    owned["responses" if first is None else "reconciliations"].append(stored)
    _bounded(owned)
    effective_responses(owned, entries)
    return owned


def assess_v3(plan, root, now=None):
    from ladon.investigation_correspondence_status import assess_structured

    entries = validated_entries(plan, root)
    responses = effective_responses(plan, entries)
    return assess_structured(plan, root, entries, responses, now=now)
