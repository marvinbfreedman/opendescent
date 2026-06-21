"""Transcript parsers for external descent evidence."""

from __future__ import annotations

import re
from math import prod


GROUP_RE = re.compile(r"Abelian Group isomorphic to\s+(?P<structure>[^\n]+)", re.IGNORECASE)
CYCLIC_FACTOR_RE = re.compile(r"\b(?:Z|C)\s*(?:/|_)\s*(\d+)\b", re.IGNORECASE)


def _is_power_of(value: int, prime: int) -> bool:
    if value < 1:
        return False
    while value % prime == 0 and value > 1:
        value //= prime
    return value == 1


def _normal_structure(factors: list[int]) -> str | None:
    if not factors:
        return None
    return " + ".join(f"Z/{factor}" for factor in sorted(factors))


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def parse_abelian_group_structure(raw: str) -> dict:
    """Parse an abelian group structure line such as ``Z/4 + Z/4``."""

    match = GROUP_RE.search(raw)
    structure = match.group("structure").strip() if match else None
    factors = [int(value) for value in CYCLIC_FACTOR_RE.findall(structure or "")]
    order = prod(factors) if factors else None
    exponent = max(factors) if factors else None
    two_primary = bool(factors) and all(_is_power_of(factor, 2) for factor in factors)
    return {
        "structure": structure,
        "cyclicFactors": sorted(factors),
        "normalizedStructure": _normal_structure(factors),
        "order": order,
        "exponent": exponent,
        "twoPrimary": two_primary,
        "higherTwoPowerDetected": two_primary and any(factor >= 4 for factor in factors),
    }


def parse_selmer_group_order(raw: str) -> int | None:
    """Extract a reported Selmer-group order from a calculator transcript."""
    parsed = parse_abelian_group_structure(raw)
    if parsed["order"] is not None:
        return parsed["order"]
    head = raw
    generator_at = raw.find("\nG.")
    if generator_at >= 0:
        head = raw[:generator_at]
    matches = re.findall(r"(?m)^(\d+)\s*$", head)
    if not matches:
        return None
    return int(matches[-1])


def parse_three_selmer_order(raw: str) -> int | None:
    """Extract the reported ThreeSelmerGroup order from a Magma transcript."""
    return parse_selmer_group_order(raw)


def selmer_group_evidence(
    label: str,
    raw: str,
    prime: int,
    expected_order: int | None = None,
    expected_structure: str | None = None,
    grh: bool = False,
    source: str | None = None,
    function_name: str | None = None,
    kind: str | None = None,
) -> dict:
    parsed = parse_abelian_group_structure(raw)
    order = parsed["order"] if parsed["order"] is not None else parse_selmer_group_order(raw)
    expected = parse_abelian_group_structure(
        f"Abelian Group isomorphic to {expected_structure}"
    ) if expected_structure else {}
    expected_factors = expected.get("cyclicFactors")
    expected_order_int = _int_or_none(expected_order)
    structure_matches = (
        parsed["cyclicFactors"] == expected_factors
        if expected_factors
        else None
    )
    order_matches = (
        order == expected_order_int
        if expected_order_int is not None and order is not None
        else None
    )
    prime_primary = (
        bool(parsed["cyclicFactors"])
        and all(_is_power_of(factor, prime) for factor in parsed["cyclicFactors"])
    )
    vector_dimension = None
    if prime_primary and parsed["cyclicFactors"] and all(factor == prime for factor in parsed["cyclicFactors"]):
        vector_dimension = len(parsed["cyclicFactors"])

    if not parsed["cyclicFactors"] and order is None:
        status = "no_selmer_group_detected"
    elif parsed["cyclicFactors"] and not prime_primary:
        status = "non_prime_primary_structure"
    elif structure_matches is False or order_matches is False:
        status = "selmer_group_mismatch"
    elif structure_matches or order_matches:
        status = "selmer_group_match"
    else:
        status = "selmer_group_detected"

    return {
        "label": label,
        "kind": kind or f"{prime}_selmer_group",
        "function": function_name or f"{prime}SelmerGroup(E)",
        "prime": prime,
        "source": source,
        "conditional": bool(grh),
        "condition": "GRH" if grh else None,
        "structure": parsed["structure"],
        "normalizedStructure": parsed["normalizedStructure"],
        "cyclicFactors": parsed["cyclicFactors"],
        "order": order,
        "exponent": parsed["exponent"],
        "primePrimary": prime_primary,
        "vectorSpaceDimension": vector_dimension,
        "expectedStructure": expected_structure,
        "expectedOrder": expected_order,
        "matchesExpectedStructure": structure_matches,
        "matchesExpectedOrder": order_matches,
        "status": status,
        "rawLineCount": len(raw.splitlines()),
    }


def three_selmer_evidence(
    label: str,
    raw: str,
    expected_order: int | None,
    grh: bool = False,
    source: str | None = None,
) -> dict:
    order = parse_three_selmer_order(raw)
    matches = order is not None and expected_order is not None and order == expected_order
    return {
        "label": label,
        "kind": "magma_three_selmer_transcript",
        "source": source,
        "conditional": bool(grh),
        "condition": "GRH" if grh else None,
        "threeSelmerOrder": order,
        "expectedSelmerOrder": expected_order,
        "matchesExpected": matches,
        "status": (
            "conditional_match"
            if grh and matches
            else "conditional_mismatch"
            if grh
            else "unconditional_match"
            if matches
            else "unconditional_mismatch"
        ),
        "rawLineCount": len(raw.splitlines()),
    }


def higher_two_power_evidence(
    label: str,
    raw: str,
    expected_structure: str | None = None,
    expected_order: int | None = None,
    grh: bool = False,
    source: str | None = None,
    computation_kind: str | None = None,
) -> dict:
    parsed = parse_abelian_group_structure(raw)
    expected = parse_abelian_group_structure(
        f"Abelian Group isomorphic to {expected_structure}"
    ) if expected_structure else {}
    expected_factors = expected.get("cyclicFactors")
    expected_order_int = _int_or_none(expected_order)
    structure_matches = (
        parsed["cyclicFactors"] == expected_factors
        if expected_factors
        else None
    )
    order_matches = (
        parsed["order"] == expected_order_int
        if expected_order_int is not None and parsed["order"] is not None
        else None
    )

    if not parsed["cyclicFactors"]:
        status = "no_group_structure_detected"
    elif not parsed["twoPrimary"]:
        status = "non_two_primary_structure"
    elif structure_matches is False or order_matches is False:
        status = "higher_two_power_mismatch"
    elif parsed["higherTwoPowerDetected"]:
        status = "higher_two_power_match" if (structure_matches or order_matches) else "higher_two_power_detected"
    else:
        status = "two_primary_but_no_higher_two_power"

    return {
        "label": label,
        "kind": computation_kind or "higher_two_power_transcript",
        "source": source,
        "conditional": bool(grh),
        "condition": "GRH" if grh else None,
        "structure": parsed["structure"],
        "normalizedStructure": parsed["normalizedStructure"],
        "cyclicFactors": parsed["cyclicFactors"],
        "order": parsed["order"],
        "exponent": parsed["exponent"],
        "twoPrimary": parsed["twoPrimary"],
        "higherTwoPowerDetected": parsed["higherTwoPowerDetected"],
        "expectedStructure": expected_structure,
        "expectedOrder": expected_order,
        "matchesExpectedStructure": structure_matches,
        "matchesExpectedOrder": order_matches,
        "status": status,
        "rawLineCount": len(raw.splitlines()),
    }
