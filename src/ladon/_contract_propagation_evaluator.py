"""Invocation-local bounded AND/OR evaluation state.

Memoized frontiers are complete only at the depth at which they were computed.
Incomplete frontiers are never reused as negative results. Shared witnesses
contain parent references, so repeated premises cannot expand a proof tree.
"""

from itertools import product

from ladon._contract_propagation_budget import BudgetRows, OutputBudget, fingerprint
from ladon._contract_propagation_common import _plain
from ladon._contract_propagation_frontier import _merge_frontier
from ladon._contract_propagation_sources import application_witness, source_rows
from ladon._contract_propagation_transfer import _transfer
from ladon._proofir_derivation_core import _key, _ref
from ladon.proof_contract_rules import PROFILE_DIGEST


class Evaluation:
    """Mutable bookkeeping is owned by one invocation and never shared globally."""

    def __init__(self, graph, contracts, bindings, interfaces, scopes, caps, deadline_observation, count):
        self.graph, self.contracts, self.bindings = graph, contracts, bindings
        self.interfaces, self.scopes = interfaces, scopes
        self.caps, self.deadline_observation = caps, deadline_observation
        self.budget = OutputBudget(caps["maxOutputBytes"])
        self.residuals, self.pending, self.prunings = (BudgetRows(self.budget) for _ in range(3))
        self.route_rows = {}
        self.counts = {"steps": 0, "combinations": 0, "references": count}
        self.memo, self.frontiers, self.active, self.witnesses = {}, {}, set(), {}
        self.uncertainty = 0
        self.source_interfaces = {
            (row["contractRef"]["artifactRef"], row["contractRef"]["localId"]): row
            for row in interfaces.values()
            if "contractRef" in row
        }

    def expired(self):
        return self.deadline_observation.expired()

    def stop(self, code, statement, *, reached, **details):
        if reached:
            self.uncertainty += 1
            self.pending.append({"code": code, "statementRef": _ref(statement), **details})
        return reached

    def witness_budget_exhausted(self, statement):
        return self.stop(
            "witness-candidate-cap",
            statement,
            reached=len(self.witnesses) >= self.caps["maxWitnessCandidates"],
        )

    def route_row(self, record, witness):
        identity = "sha256:" + fingerprint(witness).hex()
        if identity in self.route_rows:
            return self.route_rows[identity]
        row = {
            "contractRecord": record,
            "routeWitness": witness,
            "routeWitnessRef": identity,
            "routeWitnessRefs": [identity],
        }
        wire = {"witnessRef": identity, "routeWitness": witness}
        # The complete row is present in a frontier; the witness also appears
        # in the shared table. Extra route IDs from equivalence merging are
        # smaller than these fully charged rows.
        if not self.budget.reserve([row, wire], overhead=16):
            return None
        self.witnesses[identity] = witness
        self.route_rows[identity] = row
        return row

    def evaluate(self, statement, depth=0):
        if self.budget.exhausted or not self.ensure_frontier(statement):
            return []
        if self.stop("deadline", statement, reached=self.expired()):
            return []
        if self.stop("depth-cap", statement, reached=depth > self.caps["maxDepth"]):
            return []
        if statement in self.active:
            self.uncertainty += 1
            self.residuals.append({"code": "unsupported-cycle", "statementRef": _ref(statement)})
            return []
        key = (statement, depth)
        if key in self.memo:
            return self.memo[key]
        return self.evaluate_uncached(statement, depth)

    def ensure_frontier(self, statement):
        if statement in self.frontiers:
            return True
        header = {"statementRef": _ref(statement), "contracts": []}
        if not self.budget.reserve(header):
            return False
        self.frontiers[statement] = []
        return True

    def evaluate_uncached(self, statement, depth):
        before = (self.uncertainty, len(self.residuals), len(self.pending))
        self.active.add(statement)
        rows = source_rows(self, statement)
        for raw_step in self.graph.by_conclusion.get(statement, ()):
            step = _plain(raw_step)
            if self.step_stopped(statement, step):
                break
            self.counts["steps"] += 1
            rows.extend(self.evaluate_step(statement, step, depth))
        self.active.remove(statement)
        rows = _merge_frontier(
            rows,
            limit=self.caps["maxFrontierContractsPerStatement"],
            prunings=self.prunings,
            statement=_ref(statement),
            pending=self.pending,
        )
        if not rows:
            self.uncertainty += 1
            self.residuals.append(
                {"code": "missing-source-contract", "statementRef": _ref(statement)}
            )
        self.frontiers[statement] = _merge_frontier(
            self.frontiers[statement] + rows,
            limit=self.caps["maxFrontierContractsPerStatement"],
            prunings=self.prunings,
            statement=_ref(statement),
            pending=self.pending,
        )
        after = (self.uncertainty, len(self.residuals), len(self.pending))
        if before == after and not any((self.pending, self.residuals, self.budget.exhausted)):
            self.memo[(statement, depth)] = rows
        return rows

    def step_stopped(self, statement, step):
        if self.budget.exhausted:
            return True
        if self.stop("deadline", statement, reached=self.expired(), stepRef=step["stepRef"]):
            return True
        return self.stop(
            "step-cap",
            statement,
            stepRef=step["stepRef"],
            reached=self.counts["steps"] >= self.caps["maxEvaluatedSteps"],
        )

    def binding(self, step):
        binding = self.bindings.get(_key(step["stepRef"]))
        if binding is None:
            self.residuals.append({"code": "missing-rule-binding", "stepRef": step["stepRef"]})
            return None
        code = _binding_obstruction(step, binding, self.interfaces)
        if code:
            self.residuals.append(
                {"code": code, "stepRef": step["stepRef"], "ruleId": binding["ruleId"]}
            )
            return None
        return binding

    def evaluate_step(self, statement, step, depth):
        binding = self.binding(step)
        if binding is None:
            self.uncertainty += 1
            return []
        frontiers = [self.evaluate(_key(premise), depth + 1) for premise in step["premiseRefs"]]
        missing = [i for i, frontier in enumerate(frontiers) if not frontier]
        if missing:
            self.uncertainty += 1
            self.residuals.extend(
                {
                    "code": "missing-premise-contract",
                    "stepRef": step["stepRef"],
                    "statementRef": _ref(statement),
                    "premiseOrdinal": i,
                }
                for i in missing
            )
            return []
        return self.combinations(statement, step, binding, frontiers)

    def combination_stopped(self, statement, step, count):
        if self.budget.exhausted:
            return True
        if self.stop("deadline", statement, reached=self.expired(), stepRef=step["stepRef"]):
            return True
        step_full = count >= self.caps["maxCombinationsPerStep"]
        full = step_full or self.counts["combinations"] >= self.caps["maxTotalCombinations"]
        return self.stop(
            "combination-cap",
            statement,
            reached=full,
            stepRef=step["stepRef"],
            scope="step" if step_full else "analysis",
        )

    def transfer_fits(self, binding, combo):
        records = [item["contractRecord"] for item in combo]
        evidence = self.interfaces[binding["outputInterfaceId"]]["evidenceRefs"]
        return self.budget.admits([records, evidence])

    def combinations(self, statement, step, binding, frontiers):
        rows = []
        for count, combo in enumerate(product(*frontiers)):
            if self.combination_stopped(statement, step, count):
                break
            if self.witness_budget_exhausted(statement):
                break
            if not self.transfer_fits(binding, combo):
                break
            self.counts["combinations"] += 1
            record = _transfer(step, binding, combo, self.interfaces, self.graph, self.residuals)
            if record is None:
                self.uncertainty += 1
                continue
            witness = application_witness(step, binding, combo, self.interfaces)
            row = self.route_row(record, witness)
            if row is None:
                break
            rows.append(row)
        return rows


def _binding_obstruction(step, binding, interfaces):
    if binding["profileDigest"] != PROFILE_DIGEST:
        return "profile-mismatch"
    expected = {"identity": 1, "weaken-loss": 1, "compose": 2, "combine-estimates": 2}.get(
        binding["ruleId"]
    )
    if expected is None:
        return "unsupported-rule"
    if expected != len(step["premiseRefs"]) or binding["arity"] != expected:
        return "arity-mismatch"
    if not _side_conditions(binding, interfaces):
        return "unsupported-rule-side-condition"
    return None


def _side_conditions(binding, interfaces):
    parameters, rule = binding["parameters"], binding["ruleId"]
    if rule == "weaken-loss":
        return bool(parameters.get("nestednessRefs"))
    if rule == "combine-estimates":
        return all(
            parameters.get(key)
            for key in ("leftEmbeddingRefs", "rightEmbeddingRefs", "nestednessRefs")
        )
    if rule == "compose":
        return (
            parameters.get("compositeOperatorId")
            == interfaces[binding["outputInterfaceId"]]["operatorId"]
        )
    return True
