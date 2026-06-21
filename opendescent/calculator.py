"""Calculator-style arithmetic entry points."""

from __future__ import annotations

from .curve import EllipticCurve
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
) -> dict:
    """Return auditable FiveSelmerGroup(E) evidence.

    OpenDescent does not yet compute 5-Selmer groups natively.  This function
    is therefore a calculator primitive for imported backend output: pass a
    transcript containing a group line such as ``Z/5 + Z/5`` or a reported order.
    """

    label = _curve_label(curve)
    if transcript is None:
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
