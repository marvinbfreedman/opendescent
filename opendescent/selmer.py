"""Native 2-Selmer computation placeholder."""

from __future__ import annotations

from .curve import EllipticCurve


def two_selmer_certificate(curve: EllipticCurve) -> dict:
    return {
        "curve": curve.label,
        "engine": "opendescent-native",
        "twoSelmerRank": None,
        "rankUpperBound": None,
        "rankCertified": False,
        "implemented": False,
        "status": "gap: native 2-Selmer computation not implemented yet",
    }
