"""Certificate generation."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from .curve import EllipticCurve
from .finite_field import ap, primes_upto
from .local import bad_primes, reduction_record


def curve_certificate(curve: EllipticCurve, point_bound: int = 50, prime_bound: int = 31) -> dict:
    inv = curve.invariants()
    bad = bad_primes(curve)
    good_rows = []
    for p in primes_upto(prime_bound):
        if p in bad:
            continue
        good_rows.append({"p": p, "a_p": ap(curve, p)})

    pts = curve.integral_points(point_bound)
    return {
        "label": curve.label,
        "conductor": curve.conductor,
        "weierstrass": curve.weierstrass,
        "invariants": inv,
        "badPrimes": bad,
        "localRecords": [reduction_record(curve, p) for p in bad],
        "goodPrimeSamples": good_rows,
        "integralPointSearch": {
            "bound": point_bound,
            "count": len(pts),
            "points": [p.as_pair() for p in pts[:50]],
            "truncated": len(pts) > 50,
        },
        "descent": {
            "engine": "opendescent-native",
            "twoSelmerRank": None,
            "rankLowerBound": None,
            "rankUpperBound": None,
            "rankCertified": False,
            "status": "gap: native 2-descent not implemented yet",
        },
    }


def run_sage_backend(input_path: str) -> dict:
    env = dict(os.environ)
    cwd = os.getcwd()
    env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        ["sage", "-python", "-m", "opendescent.sage_backend", input_path],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    result = {
        "command": "sage -python -m opendescent.sage_backend",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "succeeded": proc.returncode == 0,
        "parsed": None,
    }
    try:
        result["parsed"] = json.loads(proc.stdout)
    except Exception:
        pass
    return result


def merge_backend(cert: dict, backend_rows: dict) -> dict:
    row = backend_rows.get(cert["label"])
    if not isinstance(row, dict):
        return cert
    cert["descent"] = {
        "engine": row.get("engine"),
        "twoSelmerRank": row.get("twoSelmerRank"),
        "selmerUpperBound": row.get("selmerUpperBound"),
        "rankLowerBound": row.get("rankLowerBound"),
        "rankUpperBound": row.get("rankUpperBound"),
        "rankInterval": row.get("rankInterval"),
        "rankCertified": row.get("rankCertified"),
        "torsionOrder": row.get("torsionOrder"),
        "rankSource": row.get("rankSource"),
        "selmerSource": row.get("selmerSource"),
        "selmerError": row.get("selmerError"),
        "status": row.get("status"),
    }
    return cert


def build_certificate(
    payload: dict,
    point_bound: int = 50,
    prime_bound: int = 31,
    backend: str = "native",
    input_path: str | None = None,
) -> dict:
    backend_result = None
    backend_rows = {}
    if backend == "sage":
        if input_path is None:
            raise ValueError("input_path is required for the Sage backend")
        backend_result = run_sage_backend(input_path)
        parsed = backend_result.get("parsed")
        if isinstance(parsed, dict) and isinstance(parsed.get("curves"), dict):
            backend_rows = parsed["curves"]

    curves = []
    for row in payload.get("curves", []):
        curve = EllipticCurve.from_weierstrass(
            row["weierstrass"],
            label=row.get("label", "curve"),
            conductor=row.get("conductor"),
        )
        cert = curve_certificate(curve, point_bound=point_bound, prime_bound=prime_bound)
        cert = merge_backend(cert, backend_rows)
        if "knownRank" in row:
            cert["knownRank"] = row["knownRank"]
        curves.append(cert)

    return {
        "artifact": "opendescent_certificate",
        "version": "0.1.0",
        "status": (
            "sage-backed rank certificate"
            if backend == "sage" and backend_result and backend_result.get("succeeded")
            else "arithmetic scaffold; descent gap explicit"
        ),
        "backend": backend,
        "backendResult": backend_result,
        "curves": curves,
        "remainingWork": [
            "full Tate algorithm",
            "2-covering construction",
            "local solubility for coverings",
            "2-Selmer upper bound",
            "Mordell-Weil rank certificate",
        ],
    }
