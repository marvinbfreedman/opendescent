"""Calculator-style arithmetic entry points."""

from __future__ import annotations

from .cassels import cassels_pairing
from .curve import EllipticCurve
from .five_descent import native_five_coverings, native_five_descent
from .transcripts import selmer_group_evidence


def _curve_label(curve: EllipticCurve | dict | object) -> str:
    if isinstance(curve, dict):
        return str(curve.get("label", "curve"))
    return str(getattr(curve, "label", "curve"))


def FiveSelmerGroup(
    curve: EllipticCurve | dict | object,
    transcript: str | None = None,
    expected_order: int | None = None,
    expected_structure: str | None = None,
    grh: bool = False,
    source: str | None = None,
    mode: str = "native",
    search_bound: int = 50,
) -> dict:
    """Return auditable FiveSelmerGroup(E) evidence.

    Transcript input is treated as imported evidence.  Without a transcript,
    ``mode="native"`` runs the native 5-descent task scaffold and reports the
    current partial proof state.
    """

    label = _curve_label(curve)
    if transcript is None:
        if mode == "native" and isinstance(curve, EllipticCurve):
            return native_five_descent(curve, search_bound=search_bound).to_json()
        return {
            "label": label,
            "kind": "five_selmer_group",
            "function": "FiveSelmerGroup(E)",
            "prime": 5,
            "available": False,
            "computed": False,
            "status": "unavailable",
            "reason": "native FiveSelmerGroup(E) computation is not implemented; provide a transcript/backend output",
        }

    evidence = selmer_group_evidence(
        label,
        transcript,
        prime=5,
        expected_order=expected_order,
        expected_structure=expected_structure,
        grh=grh,
        source=source,
        function_name="FiveSelmerGroup(E)",
        kind="five_selmer_group",
    )
    evidence["available"] = True
    evidence["computed"] = evidence["order"] is not None or bool(evidence["cyclicFactors"])
    return evidence


def FiveCoverings(curve: EllipticCurve, search_bound: int = 50) -> dict:
    return native_five_coverings(curve, search_bound=search_bound)


def CasselsPairing(curve: EllipticCurve, coverings: list[dict], prime: int = 5) -> dict:
    return cassels_pairing(curve, coverings, prime=prime).to_json()
