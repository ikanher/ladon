"""Small authored native contracts; no fixture asserts theorem authority."""

from copy import deepcopy

from support.proofir_v3_native import ENVIRONMENT, envelope, ref


def contract_record():
    return {
        "profileId": "norm-scale-v1",
        "endpointId": "estimate:f",
        "context": {
            "objectId": "operator:f", "domainId": "domain:X",
            "scaleId": "scale:N", "representationId": "representation:original",
        },
        "telescope": [{"binderId": "u", "typeId": "Nat", "quantifier": "forall"}],
        "assumptions": [{"predicateId": "input:valid"}],
        "conclusionId": "estimate:bound",
        "features": {
            "regularity": {
                "state": "known", "scaleId": "scale:N", "offset": 3, "reason": None,
            },
            "constantDependencies": {
                "state": "known", "allowedBinderIds": ["u"], "reason": None,
            },
            "witnessDependencies": [],
        },
    }


def contract_artifact():
    from ladon.proof_contract_rules import PROFILE_DIGEST

    subjects = [ref("contract", "contract:f"), ref("statement", "statement:f"),
                ref("statement", "input:valid"), ref("statement", "estimate:bound"),
                ref("source-map", "source:f")]
    return envelope("proofir.contract", {
        "contractId": "contract:f", "profileDigest": PROFILE_DIGEST,
        "record": contract_record(), "statementRef": subjects[1],
        "assumptionRefs": [subjects[2]], "conclusionRef": subjects[3],
        "sourceMapRefs": [subjects[4]], "checkRunRefs": [],
        "provenance": {
            "mode": "authored", "fidelity": "attributed-unreviewed",
            "completeness": "complete", "checkerAuthority": "none",
            "mathematicalFalsity": "not-established",
        },
        "residuals": [],
    }, deepcopy(subjects), environment=ENVIRONMENT)
