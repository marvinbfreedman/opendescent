"""Native Tate algorithm placeholder.

This module reserves the public interface for the native Tate algorithm.  It is
deliberately non-certifying until the full additive and non-minimal cases are
implemented.
"""

from __future__ import annotations

from .curve import EllipticCurve


def tate_algorithm(curve: EllipticCurve, p: int) -> dict:
    return {
        "p": p,
        "curve": curve.label,
        "implemented": False,
        "status": "gap: native full Tate algorithm not implemented yet",
    }
