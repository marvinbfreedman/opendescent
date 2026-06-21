"""Native 5-descent task scaffolding.

The module intentionally separates task construction from certification.  It
records the native inputs OpenDescent can compute today and marks the missing
general 5-covering kernels explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .curve import EllipticCurve, Point
from .local import bad_primes


def five_descent_prime_set(curve: EllipticCurve) -> list[int]:
    primes = set(bad_primes(curve))
    primes.add(5)
    return sorted(primes)


def _point_to_string(point: Point) -> str:
    if point.is_infinity:
        return "O"
    return f"[{point.x}:{point.y}:1]"


def rational_p_torsion_candidates(curve: EllipticCurve, p: int = 5, search_bound: int = 50) -> list[dict]:
    candidates = []
    seen = set()
    for point in curve.integral_points(search_bound):
        if curve.mul(p, point).is_infinity and not curve.mul(1, point).is_infinity:
            key = point.as_pair()
            key_text = repr(key)
            if key_text in seen:
                continue
            seen.add(key_text)
            candidates.append(
                {
                    "point": _point_to_string(point),
                    "orderDivides": p,
                    "source": f"integral point search bound {search_bound}",
                }
            )
    return candidates


@dataclass(frozen=True)
class FiveDescentTask:
    curve: str
    weierstrass: list[int]
    local_primes: list[int]
    search_bound: int
    kernel_status: str = "missing_general_5_covering_kernel"

    def to_json(self) -> dict:
        return {
            "curve": self.curve,
            "weierstrass": self.weierstrass,
            "localPrimes": self.local_primes,
            "searchBound": self.search_bound,
            "kernelStatus": self.kernel_status,
        }


@dataclass
class FiveCovering:
    label: str
    equations: list[str] = field(default_factory=list)
    coordinates: list[str] = field(default_factory=list)
    local_obstructions: dict[str, str] = field(default_factory=dict)
    provenance: str = "native"
    cassels_values: dict[str, int] = field(default_factory=dict)
    vector: list[int] | None = None

    def to_json(self) -> dict:
        return {
            "label": self.label,
            "equations": self.equations,
            "coordinates": self.coordinates,
            "localObstructions": self.local_obstructions,
            "provenance": self.provenance,
            "casselsValues": dict(sorted(self.cassels_values.items())),
            "vector": self.vector,
        }

    @classmethod
    def from_obj(cls, value: "FiveCovering | dict") -> "FiveCovering":
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise TypeError("covering must be a FiveCovering or dict")
        return cls(
            label=str(value.get("label", "covering")),
            equations=list(value.get("equations", [])),
            coordinates=list(value.get("coordinates", [])),
            local_obstructions=dict(value.get("localObstructions", value.get("local_obstructions", {}))),
            provenance=str(value.get("provenance", "native")),
            cassels_values={str(k): int(v) for k, v in dict(value.get("casselsValues", {})).items()},
            vector=list(value["vector"]) if value.get("vector") is not None else None,
        )


@dataclass
class FiveSelmerResult:
    label: str
    task: FiveDescentTask
    coverings: list[FiveCovering]
    rational_torsion_candidates: list[dict]
    status: str
    computed: bool
    missing_steps: list[str]

    def to_json(self) -> dict:
        elementary_dimension = None
        if self.computed and self.coverings:
            elementary_dimension = len(self.coverings)
        return {
            "label": self.label,
            "kind": "native_five_descent",
            "function": "FiveSelmerGroup(E)",
            "prime": 5,
            "source": "native",
            "computed": self.computed,
            "status": self.status,
            "task": self.task.to_json(),
            "coverings": [covering.to_json() for covering in self.coverings],
            "acceptedCoveringCount": len(self.coverings),
            "rationalFiveTorsionCandidates": self.rational_torsion_candidates,
            "vectorSpaceDimension": elementary_dimension,
            "order": None if elementary_dimension is None else 5**elementary_dimension,
            "normalizedStructure": (
                None
                if elementary_dimension is None
                else " + ".join(["Z/5"] * elementary_dimension)
            ),
            "missingSteps": self.missing_steps,
        }


def native_five_descent(curve: EllipticCurve, search_bound: int = 50) -> FiveSelmerResult:
    task = FiveDescentTask(
        curve=curve.label,
        weierstrass=curve.weierstrass,
        local_primes=five_descent_prime_set(curve),
        search_bound=search_bound,
    )
    torsion = rational_p_torsion_candidates(curve, 5, search_bound=search_bound)
    missing = [
        "construct degree-5 genus-one normal curve representatives",
        "run local solubility for 5-coverings",
        "compute relations among accepted 5-coverings",
    ]
    return FiveSelmerResult(
        label=curve.label,
        task=task,
        coverings=[],
        rational_torsion_candidates=torsion,
        status="partial: native general 5-descent task created but covering kernel is not implemented",
        computed=False,
        missing_steps=missing,
    )


def native_five_coverings(curve: EllipticCurve, search_bound: int = 50) -> dict:
    result = native_five_descent(curve, search_bound=search_bound)
    return {
        "label": curve.label,
        "kind": "native_five_coverings",
        "prime": 5,
        "source": "native",
        "computed": False,
        "status": "partial: native 5-covering construction is not implemented",
        "task": result.task.to_json(),
        "coverings": [],
        "missingSteps": result.missing_steps,
    }
