"""Native 2-covering construction placeholder."""

from __future__ import annotations

from .curve import EllipticCurve


def two_coverings(curve: EllipticCurve) -> dict:
    return {
        "curve": curve.label,
        "implemented": False,
        "coverings": [],
        "status": "gap: native 2-covering construction not implemented yet",
    }
