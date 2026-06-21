"""Native local-solubility checks for 2-coverings placeholder."""

from __future__ import annotations


def local_solubility_report(covering: dict, primes: list[int]) -> dict:
    return {
        "covering": covering,
        "primes": primes,
        "implemented": False,
        "status": "gap: native local solubility checks not implemented yet",
    }
