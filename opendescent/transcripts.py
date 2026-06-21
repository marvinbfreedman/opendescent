"""Transcript parsers for external descent evidence."""

from __future__ import annotations

import re


def parse_three_selmer_order(raw: str) -> int | None:
    """Extract the reported ThreeSelmerGroup order from a Magma transcript."""
    head = raw
    generator_at = raw.find("\nG.")
    if generator_at >= 0:
        head = raw[:generator_at]
    matches = re.findall(r"(?m)^(\d+)\s*$", head)
    if not matches:
        return None
    return int(matches[-1])


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
