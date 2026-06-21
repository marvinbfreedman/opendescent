"""Higher-descent and Cassels-pairing certificate helpers."""

from __future__ import annotations

import re


SECOND_DESCENT_RE = re.compile(r"Second step,\s*determining 2nd descent Selmer groups", re.IGNORECASE)
FULL_TWO_DESCENT_RE = re.compile(r"Used full 2-descent via multiplication-by-2 map", re.IGNORECASE)
ISOGENY_DESCENT_RE = re.compile(
    r"Used descent via 2-isogeny with isogenous curve E'\s*=\s*(?P<curve>\[[^\n]+\])",
    re.IGNORECASE,
)

DIMENSION_PATTERNS = {
    "rankBoundAfterFirstDescent": r"After first local descent,\s*rank bound\s*=\s*(\d+)",
    "rankBoundAfterSecondDescent": r"After second local descent,\s*rank bound\s*=\s*(\d+)",
    "rankS2E": r"(?:rk\(S\^\{2\}\(E\)\)|Rank of S\^2\(E\))\s*=\s*(\d+)",
    "rankS2EPrime": r"(?:rk\(S\^\{2\}\(E'\)\)|Rank of S\^2\(E'\))\s*=\s*(\d+)",
    "rankSPhiEPrime": r"(?:rk\(S\^\{phi\}\(E'\)\)|Rank of S\^phi\(E'\))\s*=\s*(\d+)",
    "rankSPhiPrimeE": r"(?:rk\(S\^\{phi'\}\(E\)\)|Rank of S\^phi'\(E\))\s*=\s*(\d+)",
    "rankPhiPrimeS2E": r"rk\(phi'\(S\^\{2\}\(E\)\)\)\s*=\s*(\d+)",
    "rankPhiS2EPrime": r"rk\(phi\(S\^\{2\}\(E'\)\)\)\s*=\s*(\d+)",
}

SHA_PATTERNS = {
    "shaE_phiPrime": r"#III\(E/Q\)\[phi'\]\s*=\s*(\d+)",
    "shaE_two": r"#III\(E/Q\)\[2\]\s*=\s*(\d+)",
    "shaEPrime_phiPrimeImage": r"#phi'\(III\(E/Q\)\[2\]\)\s*=\s*(\d+)",
    "shaEPrime_phi": r"#III\(E'/Q\)\[phi\]\s*=\s*(\d+)",
    "shaEPrime_two": r"#III\(E'/Q\)\[2\]\s*=\s*(\d+)",
}


def _first_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None


def _extract_ints(patterns: dict[str, str], text: str) -> dict:
    values = {}
    for key, pattern in patterns.items():
        value = _first_int(pattern, text)
        if value is not None:
            values[key] = value
    return values


def cassels_pairing_placeholder(
    engine: str,
    reason: str | None = None,
    available_methods: list[str] | None = None,
) -> dict:
    """Return an explicit non-claim for Cassels-pairing data.

    The certificate should say when a pairing was not computed.  This avoids
    treating Selmer or Sha-size traces as if they were a Cassels pairing matrix.
    """

    methods = available_methods or []
    return {
        "engine": engine,
        "available": bool(methods),
        "computed": False,
        "availableMethods": methods,
        "matrix": None,
        "reason": reason or "no Cassels pairing backend has been wired into OpenDescent",
        "status": (
            "Cassels pairing method detected but not executed"
            if methods
            else "Cassels pairing not computed"
        ),
    }


def native_higher_two_descent_placeholder() -> dict:
    return {
        "engine": "opendescent-native",
        "available": False,
        "computed": False,
        "secondDescentDetected": False,
        "method": None,
        "status": "gap: native higher 2-descent is not implemented yet",
    }


def sage_higher_two_descent_capabilities(methods: list[str]) -> dict:
    return {
        "engine": "sage",
        "available": bool(methods),
        "computed": False,
        "availableMethods": methods,
        "secondDescentDetected": False,
        "method": "Sage capability probe",
        "status": (
            "Sage exposes descent methods; OpenDescent does not run higher 2-descent by default"
            if methods
            else "no Sage descent methods detected"
        ),
    }


def parse_mwrank_higher_two_descent(output: str) -> dict:
    second = bool(SECOND_DESCENT_RE.search(output))
    full = bool(FULL_TWO_DESCENT_RE.search(output))
    isogeny_match = ISOGENY_DESCENT_RE.search(output)
    isogeny_curve = isogeny_match.group("curve").strip() if isogeny_match else None
    isogeny = isogeny_curve is not None or "Using 2-isogenous curve" in output
    dimensions = _extract_ints(DIMENSION_PATTERNS, output)
    sha_info = _extract_ints(SHA_PATTERNS, output)

    if second and isogeny:
        method = "2-isogeny descent with second local descent"
        status = "higher 2-descent evidence parsed from mwrank second descent step"
    elif isogeny:
        method = "2-isogeny descent"
        status = "2-isogeny descent evidence parsed; no second step detected"
    elif full:
        method = "full 2-descent via multiplication-by-2 map"
        status = "ordinary full 2-descent evidence parsed; no higher step detected"
    else:
        method = None
        status = "no higher 2-descent evidence found in mwrank output"

    return {
        "engine": "mwrank",
        "available": True,
        "computed": bool(second or full or isogeny or dimensions),
        "method": method,
        "secondDescentDetected": second,
        "isogenyDescentDetected": isogeny,
        "fullMultiplicationByTwoDetected": full,
        "isogenousCurve": isogeny_curve,
        "selmerDimensions": dimensions,
        "shaTwoInformation": sha_info,
        "status": status,
    }
