"""Sage-backed odd-primary Sha evidence.

This module is deliberately narrower than a Selmer-group implementation.  It
uses Sage's provable Sha primary-order helpers where available and records
bound-only output as non-certifying evidence.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


SAGE_PRIMARY_PROBE = r'''
import json
import sys
import traceback

from sage.all import EllipticCurve, QQ


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, bool) or value is None:
        return value
    try:
        return int(value)
    except Exception:
        return str(value)


def capture(out, key, func):
    try:
        out[key] = jsonable(func())
    except Exception as exc:
        out[key] = None
        out.setdefault("errors", {})[key] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }


payload = json.load(open(sys.argv[1]))
label = payload.get("label", "curve")
prime = int(payload["prime"])
coeffs = payload["weierstrass"]
out = {
    "label": label,
    "prime": prime,
    "weierstrass": coeffs,
    "backend": "sage",
    "success": True,
    "errors": {},
}

try:
    E = EllipticCurve(QQ, coeffs)
    sha = E.sha()
    capture(out, "rankBounds", lambda: E.rank_bounds())
    capture(out, "analyticRank", lambda: E.analytic_rank())
    capture(out, "torsionOrder", lambda: E.torsion_subgroup().order())
    capture(out, "shaBound", lambda: sha.bound())
    if prime == 2:
        capture(out, "twoSelmerBound", lambda: sha.two_selmer_bound())
    else:
        capture(out, "pPrimaryBoundExponent", lambda: sha.p_primary_bound(prime))
        capture(out, "pPrimaryOrderExponent", lambda: sha.p_primary_order(prime))
except Exception as exc:
    out["success"] = False
    out["fatalError"] = {
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }

print(json.dumps(out, sort_keys=True))
'''


def expected_exponent(prime: int, order: int | None) -> int | None:
    if order is None or order < 1 or prime < 2:
        return None
    exponent = 0
    value = int(order)
    while value % prime == 0 and value > 1:
        value //= prime
        exponent += 1
    return exponent if value == 1 else None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _rank_interval(raw: dict) -> list[int] | None:
    bounds = raw.get("rankBounds")
    if not isinstance(bounds, list) or len(bounds) != 2:
        return None
    lower = _int_or_none(bounds[0])
    upper = _int_or_none(bounds[1])
    if lower is None or upper is None:
        return None
    return [lower, upper]


def classify_primary_evidence(
    case: dict,
    raw: dict | None,
    *,
    backend_available: bool = True,
    timed_out: bool = False,
) -> dict:
    label = str(case.get("label", "curve"))
    prime = int(case["prime"])
    expected_order = _int_or_none(case.get("expectedPrimaryOrder") or case.get("targetPrimaryOrder"))
    expected_exp = expected_exponent(prime, expected_order)

    evidence = {
        "label": label,
        "prime": prime,
        "backend": "sage",
        "policy": "no_magma",
        "certified": False,
        "certificationState": "unavailable",
        "status": "sage_primary_unavailable",
        "expectedPrimaryOrder": expected_order,
        "expectedPrimaryExponent": expected_exp,
        "rankInterval": None,
        "analyticRank": None,
        "torsionOrder": None,
        "pPrimaryOrderExponent": None,
        "pPrimaryOrder": None,
        "pPrimaryBoundExponent": None,
        "pPrimaryBoundOrder": None,
        "twoSelmerBound": None,
        "shaBound": None,
        "reason": None,
        "errors": {},
    }

    if not backend_available:
        evidence["reason"] = "sage executable not found in PATH"
        return evidence
    if timed_out:
        evidence["certificationState"] = "timeout"
        evidence["reason"] = "Sage primary evidence probe timed out"
        return evidence
    if not isinstance(raw, dict):
        evidence["reason"] = "Sage primary evidence probe returned no parsed JSON"
        return evidence

    evidence["rankInterval"] = _rank_interval(raw)
    evidence["analyticRank"] = _int_or_none(raw.get("analyticRank"))
    evidence["torsionOrder"] = _int_or_none(raw.get("torsionOrder"))
    evidence["shaBound"] = raw.get("shaBound")
    evidence["errors"] = raw.get("errors") if isinstance(raw.get("errors"), dict) else {}

    if prime == 2:
        evidence["status"] = "higher_two_power_unresolved"
        evidence["certificationState"] = "requires_higher_two_power_evidence"
        evidence["twoSelmerBound"] = _int_or_none(raw.get("twoSelmerBound"))
        evidence["reason"] = (
            "ordinary 2-Selmer/Sha[2] data does not certify the required "
            "higher 2-primary structure"
        )
        return evidence

    order_exp = _int_or_none(raw.get("pPrimaryOrderExponent"))
    bound_exp = _int_or_none(raw.get("pPrimaryBoundExponent"))
    evidence["pPrimaryOrderExponent"] = order_exp
    evidence["pPrimaryBoundExponent"] = bound_exp
    if order_exp is not None:
        evidence["pPrimaryOrder"] = prime**order_exp
    if bound_exp is not None:
        evidence["pPrimaryBoundOrder"] = prime**bound_exp

    if order_exp is not None:
        if expected_exp is not None and order_exp == expected_exp:
            evidence["certified"] = True
            evidence["certificationState"] = "certified"
            evidence["status"] = "sage_primary_order_confirmed"
            evidence["reason"] = (
                f"Sage sha().p_primary_order({prime}) proves primary order "
                f"{evidence['pPrimaryOrder']}."
            )
        else:
            evidence["certificationState"] = "mismatch"
            evidence["status"] = "sage_primary_order_mismatch"
            evidence["reason"] = (
                f"Sage proved primary order {evidence['pPrimaryOrder']}, "
                f"but expected {expected_order}."
            )
        return evidence

    if bound_exp is not None:
        evidence["certificationState"] = "bounded_not_certified"
        if expected_exp is not None and bound_exp == expected_exp:
            evidence["status"] = "sage_primary_bound_matches_expected"
            evidence["reason"] = (
                f"Sage proves the {prime}-primary Sha order is at most "
                f"{evidence['pPrimaryBoundOrder']}, matching the expected "
                "exponent, but exact-order certification failed."
            )
        else:
            evidence["status"] = "sage_primary_bound_available"
            evidence["reason"] = (
                f"Sage proves a {prime}-primary upper bound of "
                f"{evidence['pPrimaryBoundOrder']}, but exact-order "
                "certification is unavailable."
            )
        return evidence

    error_bits = []
    for key in ("pPrimaryOrderExponent", "pPrimaryBoundExponent"):
        err = evidence["errors"].get(key)
        if isinstance(err, dict) and err.get("message"):
            error_bits.append(f"{key}: {err['message']}")
    evidence["reason"] = "; ".join(error_bits) or "Sage primary-order and primary-bound probes are unavailable"
    return evidence


def run_sage_primary_probe(case: dict, timeout: int = 180) -> dict:
    if shutil.which("sage") is None:
        return {
            "case": case,
            "raw": None,
            "backendAvailable": False,
            "timedOut": False,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "evidence": classify_primary_evidence(case, None, backend_available=False),
        }

    env = dict(os.environ)
    env.setdefault("DOT_SAGE", os.path.join(tempfile.gettempdir(), "opendescent-sage"))
    os.makedirs(env["DOT_SAGE"], exist_ok=True)

    payload = {
        "label": case.get("label"),
        "prime": int(case["prime"]),
        "weierstrass": case.get("weierstrass") or case.get("aInvariants"),
    }
    with tempfile.TemporaryDirectory(prefix="opendescent-sage-primary-") as tmp:
        input_path = Path(tmp) / "case.json"
        input_path.write_text(json.dumps(payload))
        try:
            proc = subprocess.run(
                ["sage", "-python", "-c", SAGE_PRIMARY_PROBE, str(input_path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            evidence = classify_primary_evidence(case, None, timed_out=True)
            return {
                "case": case,
                "raw": None,
                "backendAvailable": True,
                "timedOut": True,
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "evidence": evidence,
            }

    raw = None
    try:
        raw = json.loads(proc.stdout)
    except Exception:
        raw = None
    evidence = classify_primary_evidence(case, raw, backend_available=True)
    return {
        "case": case,
        "raw": raw,
        "backendAvailable": True,
        "timedOut": False,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "evidence": evidence,
    }
