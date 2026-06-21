"""Optional SageMath backend.

Run with:

    sage -python -m opendescent.sage_backend input.json

This open-source backend adapter lets OpenDescent consume Sage/eclib rank and
Selmer computations through the same JSON certificate protocol while native
descent is under construction.
"""

from __future__ import annotations

import json
import sys
import traceback

from sage.all import EllipticCurve, QQ

from .higher_descent import cassels_pairing_placeholder, sage_higher_two_descent_capabilities


def _int_or_none(value):
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def curve_backend(row: dict) -> dict:
    label = row.get("label", "curve")
    coeffs = row["weierstrass"]
    E = EllipticCurve(QQ, coeffs)

    lower = upper = None
    rank_source = None
    try:
        bounds = E.rank_bounds()
        lower, upper = _int_or_none(bounds[0]), _int_or_none(bounds[1])
        rank_source = "sage:rank_bounds"
    except Exception:
        rank = _int_or_none(E.rank())
        lower = upper = rank
        rank_source = "sage:rank"

    selmer_rank = None
    selmer_source = None
    selmer_error = None
    try:
        selmer_rank = _int_or_none(E.selmer_rank())
        selmer_source = "sage:selmer_rank"
    except Exception as exc:
        selmer_error = str(exc)

    torsion_order = None
    try:
        torsion_order = _int_or_none(E.torsion_subgroup().order())
    except Exception:
        pass

    descent_methods = [
        name
        for name in ("two_descent", "simon_two_descent", "selmer_rank", "three_selmer_rank")
        if hasattr(E, name)
    ]
    cassels_methods = sorted(name for name in dir(E) if "cassels" in name.lower())

    certified = lower is not None and upper is not None and lower == upper
    return {
        "label": label,
        "engine": "sage",
        "rankLowerBound": lower,
        "rankUpperBound": upper,
        "rankInterval": [lower, upper] if lower is not None and upper is not None else None,
        "rankCertified": certified,
        "twoSelmerRank": selmer_rank,
        "selmerUpperBound": selmer_rank,
        "torsionOrder": torsion_order,
        "rankSource": rank_source,
        "selmerSource": selmer_source,
        "selmerError": selmer_error,
        "higherTwoDescent": sage_higher_two_descent_capabilities(descent_methods),
        "casselsPairing": cassels_pairing_placeholder(
            "sage",
            reason="Sage backend did not compute a Cassels pairing matrix for this certificate",
            available_methods=cassels_methods,
        ),
        "status": "certified rank interval" if certified else "open rank interval",
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(json.dumps({"success": False, "error": "usage: sage -python -m opendescent.sage_backend input.json"}))
        raise SystemExit(2)

    payload = json.load(open(sys.argv[1]))
    curves = {}
    failures = {}
    for row in payload.get("curves", []):
        label = row.get("label", "curve")
        try:
            curves[label] = curve_backend(row)
        except Exception as exc:
            failures[label] = {
                "success": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }

    print(
        json.dumps(
            {
                "artifact": "opendescent_sage_backend",
                "success": not failures,
                "curves": curves,
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(0 if not failures else 1)


if __name__ == "__main__":
    main()
