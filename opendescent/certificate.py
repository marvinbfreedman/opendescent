"""Certificate generation."""

from __future__ import annotations

from .backends import available_backends, run_backend
from .curve import EllipticCurve
from .finite_field import ap, primes_upto
from .local import bad_primes, reduction_record
from .selmer import two_selmer_certificate


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
            **two_selmer_certificate(curve),
            "rankLowerBound": None,
            "rankInterval": None,
        },
    }


def merge_backend(cert: dict, backend_rows: dict) -> dict:
    row = backend_rows.get(cert["label"])
    if not isinstance(row, dict):
        return cert
    lower = row.get("rankLowerBound")
    upper = row.get("rankUpperBound")
    certified = lower is not None and upper is not None and lower == upper
    cert["descent"] = {
        "engine": row.get("engine"),
        "twoSelmerRank": row.get("twoSelmerRank"),
        "selmerUpperBound": row.get("selmerUpperBound"),
        "rankLowerBound": lower,
        "rankUpperBound": upper,
        "rankInterval": [lower, upper] if lower is not None and upper is not None else None,
        "rankCertified": certified,
        "torsionOrder": row.get("torsionOrder"),
        "rankSource": row.get("rankSource"),
        "selmerSource": row.get("selmerSource"),
        "selmerError": row.get("selmerError"),
        "status": "certified rank interval" if certified else "open rank interval",
    }
    return cert


def build_certificate(
    payload: dict,
    point_bound: int = 50,
    prime_bound: int = 31,
    backend: str = "native",
    input_path: str | None = None,
) -> dict:
    backend_result = run_backend(backend, input_path)
    backend_rows = {}
    parsed = backend_result.get("parsed") if backend_result else None
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

    all_certified = bool(curves) and all(
        curve.get("descent", {}).get("rankCertified") is True for curve in curves
    )
    backend_succeeded = backend == "native" or bool(backend_result and backend_result.get("succeeded"))

    return {
        "artifact": "opendescent_certificate",
        "version": "0.1.0",
        "status": (
            "rank certificate"
            if backend_succeeded and all_certified
            else "arithmetic scaffold; descent gap explicit"
        ),
        "backend": backend,
        "availableBackends": available_backends(),
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
