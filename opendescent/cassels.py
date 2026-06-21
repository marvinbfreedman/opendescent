"""Cassels-pairing task support."""

from __future__ import annotations

from dataclasses import dataclass

from .curve import EllipticCurve
from .f5 import is_alternating_matrix, nullspace_mod, rank_mod
from .five_descent import FiveCovering


@dataclass(frozen=True)
class CasselsPairingTask:
    curve: str
    prime: int
    covering_labels: list[str]
    source: str = "native"

    def to_json(self) -> dict:
        return {
            "curve": self.curve,
            "prime": self.prime,
            "coveringLabels": self.covering_labels,
            "source": self.source,
        }


@dataclass(frozen=True)
class CasselsPairingResult:
    task: CasselsPairingTask
    matrix: list[list[int]] | None
    computed: bool
    status: str
    missing_entries: list[list[str]]

    def to_json(self) -> dict:
        radical_basis = None
        rank = None
        alternating = None
        if self.matrix is not None:
            rank = rank_mod(self.matrix, self.task.prime)
            radical_basis = nullspace_mod(self.matrix, self.task.prime)
            alternating = is_alternating_matrix(self.matrix, self.task.prime)
        return {
            "kind": "cassels_pairing",
            "engine": "opendescent-native",
            "prime": self.task.prime,
            "source": self.task.source,
            "computed": self.computed,
            "status": self.status,
            "task": self.task.to_json(),
            "matrix": self.matrix,
            "rank": rank,
            "radicalBasis": radical_basis,
            "radicalDimension": None if radical_basis is None else len(radical_basis),
            "alternating": alternating,
            "missingEntries": self.missing_entries,
        }


def _coerce_coverings(coverings: list[FiveCovering | dict]) -> list[FiveCovering]:
    return [FiveCovering.from_obj(covering) for covering in coverings]


def cassels_pairing(
    curve: EllipticCurve,
    coverings: list[FiveCovering | dict],
    prime: int = 5,
) -> CasselsPairingResult:
    normalized = _coerce_coverings(coverings)
    labels = [covering.label for covering in normalized]
    task = CasselsPairingTask(curve=curve.label, prime=prime, covering_labels=labels)
    if prime != 5:
        return CasselsPairingResult(
            task=task,
            matrix=None,
            computed=False,
            status="unavailable: native Cassels pairing currently targets 5-coverings only",
            missing_entries=[],
        )
    if not normalized:
        return CasselsPairingResult(
            task=task,
            matrix=None,
            computed=False,
            status="partial: no native 5-covering representatives available for Cassels pairing",
            missing_entries=[],
        )

    index = {label: idx for idx, label in enumerate(labels)}
    matrix = [[0 for _ in labels] for _ in labels]
    missing: list[list[str]] = []

    for left in normalized:
        i = index[left.label]
        for right in normalized:
            j = index[right.label]
            if i == j:
                continue
            value = left.cassels_values.get(right.label)
            opposite = right.cassels_values.get(left.label)
            if value is None and opposite is None:
                if i < j:
                    missing.append([left.label, right.label])
                continue
            if value is None:
                value = -int(opposite)
            matrix[i][j] = int(value) % prime

    if missing:
        return CasselsPairingResult(
            task=task,
            matrix=matrix,
            computed=False,
            status="partial: missing Cassels pairing entries for some 5-covering pairs",
            missing_entries=missing,
        )
    if not is_alternating_matrix(matrix, prime):
        return CasselsPairingResult(
            task=task,
            matrix=matrix,
            computed=False,
            status="invalid: Cassels pairing matrix is not alternating",
            missing_entries=[],
        )
    return CasselsPairingResult(
        task=task,
        matrix=matrix,
        computed=True,
        status="computed",
        missing_entries=[],
    )
