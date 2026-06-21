"""Local reduction metadata.

This is a deliberately small public-math implementation.  It classifies good
reduction and the basic multiplicative branch.  Additive Kodaira symbols remain
an explicit gap until the full Tate algorithm is implemented.
"""

from __future__ import annotations

from math import prod

from .curve import EllipticCurve
from .finite_field import ap


def factor_int(n: int) -> dict[int, int]:
    n = abs(n)
    out: dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            out[d] = out.get(d, 0) + 1
            n //= d
        d += 1 if d == 2 else 2
    if n > 1:
        out[n] = out.get(n, 0) + 1
    return out


def valuation(n: int, p: int) -> int:
    n = abs(n)
    v = 0
    while n and n % p == 0:
        v += 1
        n //= p
    return v


def is_square_mod(a: int, p: int) -> bool:
    a %= p
    if a == 0:
        return True
    return pow(a, (p - 1) // 2, p) == 1


def reduction_record(curve: EllipticCurve, p: int) -> dict:
    inv = curve.invariants()
    delta = int(inv["discriminant"])
    c4 = int(inv["c4"])
    c6 = int(inv["c6"])
    if delta % p != 0:
        return {
            "p": p,
            "reduction": "good",
            "vDelta": 0,
            "a_p": ap(curve, p),
            "localFactor": [1, -ap(curve, p), p],
            "status": "certified good-prime point count",
        }

    v_delta = valuation(delta, p)
    if c4 % p != 0:
        split = is_square_mod(-c6, p) if p != 2 else None
        reduction = "split multiplicative" if split else "nonsplit multiplicative"
        a_bad = -1 if split else 1
        return {
            "p": p,
            "reduction": reduction,
            "vDelta": v_delta,
            "a_p": a_bad,
            "localFactor": [1, -a_bad],
            "status": "basic multiplicative criterion",
        }

    return {
        "p": p,
        "reduction": "additive or non-minimal unresolved",
        "vDelta": v_delta,
        "a_p": None,
        "localFactor": None,
        "status": "gap: full Tate algorithm not implemented",
    }


def bad_primes(curve: EllipticCurve) -> list[int]:
    return sorted(factor_int(int(curve.invariants()["discriminant"])).keys())

