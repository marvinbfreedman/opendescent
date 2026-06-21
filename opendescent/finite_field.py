"""Finite-field point counts for elliptic curves."""

from __future__ import annotations

from .curve import EllipticCurve


def count_points_mod_p(curve: EllipticCurve, p: int) -> int:
    if p <= 1:
        raise ValueError("p must be prime")
    count = 1  # point at infinity
    for x in range(p):
        rhs = (x**3 + curve.a2 * x * x + curve.a4 * x + curve.a6) % p
        for y in range(p):
            lhs = (y * y + curve.a1 * x * y + curve.a3 * y) % p
            if lhs == rhs:
                count += 1
    return count


def ap(curve: EllipticCurve, p: int) -> int:
    return p + 1 - count_points_mod_p(curve, p)


def primes_upto(n: int) -> list[int]:
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for k in range(2, int(n**0.5) + 1):
        if sieve[k]:
            step = k
            start = k * k
            sieve[start : n + 1 : step] = [False] * (((n - start) // step) + 1)
    return [i for i, ok in enumerate(sieve) if ok]

