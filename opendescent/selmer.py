"""Native 2-Selmer computation placeholder."""

from __future__ import annotations

from .curve import EllipticCurve
from .higher_descent import cassels_pairing_placeholder, native_higher_two_descent_placeholder


def two_selmer_certificate(curve: EllipticCurve) -> dict:
    return {
        "curve": curve.label,
        "engine": "opendescent-native",
        "twoSelmerRank": None,
        "rankUpperBound": None,
        "rankCertified": False,
        "implemented": False,
        "higherTwoDescent": native_higher_two_descent_placeholder(),
        "casselsPairing": cassels_pairing_placeholder("opendescent-native"),
        "status": "gap: native 2-Selmer computation not implemented yet",
    }
