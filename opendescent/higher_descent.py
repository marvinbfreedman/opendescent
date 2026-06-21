"""Higher-descent and Cassels-pairing certificate helpers."""

from __future__ import annotations

import re
from math import prod

from .transcripts import higher_two_power_evidence


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

SELMER_ORDER_RE = re.compile(r"#S\^\(2\)\(E/Q\)\s*=\s*(\d+)")
SHA_TWO_BOUND_RE = re.compile(r"#III\(E/Q\)\[2\]\s*(?P<op><=|=)\s*(?P<order>\d+)")
RANK_INTERVAL_RE = re.compile(
    r"(?P<lower>\d+)\s*<=\s*rank\s*<=\s*(?:selmer-rank\s*=\s*)?(?P<upper>\d+)",
    re.IGNORECASE,
)
RANK_BOUND_TEXT_RE = re.compile(
    r"lower bound of\s*(?P<lower>\d+)\s*and an upper bound of\s*(?P<upper>\d+)",
    re.IGNORECASE,
)
TYPE3_QUARTIC_RE = re.compile(r"^\((?P<coeffs>[-0-9,\s]+)\)\s*--(?P<body>.*)$")
NEW_CLASS_RE = re.compile(r"--new \((?P<group>[A-Z])\) #(?P<index>\d+)")
EQUIV_CLASS_RE = re.compile(r"--equivalent to \((?P<group>[A-Z])\) #(?P<index>\d+)")


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


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _two_primary_part(value: int | None) -> int | None:
    if value is None or value < 1:
        return None
    out = 1
    n = int(value)
    while n % 2 == 0:
        out *= 2
        n //= 2
    return out


def _rank_interval(output: str) -> list[int] | None:
    matches = list(RANK_INTERVAL_RE.finditer(output))
    if matches:
        match = matches[-1]
        return [int(match.group("lower")), int(match.group("upper"))]
    match = RANK_BOUND_TEXT_RE.search(output)
    if match:
        return [int(match.group("lower")), int(match.group("upper"))]
    return None


def _parse_type3_quartics(output: str) -> dict:
    rows = []
    for line in output.splitlines():
        match = TYPE3_QUARTIC_RE.match(line.strip())
        if not match:
            continue
        body = match.group("body")
        new_match = NEW_CLASS_RE.search(body)
        equiv_match = EQUIV_CLASS_RE.search(body)
        normalized_body = body.strip()
        rows.append(
            {
                "coefficients": [int(value.strip()) for value in match.group("coeffs").split(",")],
                "trivial": normalized_body.startswith("trivial"),
                "nontrivial": normalized_body.startswith("nontrivial"),
                "locallySoluble": "locally soluble" in body,
                "noRationalPointFound": "no rational point found" in body,
                "newClass": (
                    {"group": new_match.group("group"), "index": int(new_match.group("index"))}
                    if new_match
                    else None
                ),
                "equivalentClass": (
                    {"group": equiv_match.group("group"), "index": int(equiv_match.group("index"))}
                    if equiv_match
                    else None
                ),
            }
        )
    new_classes = [row["newClass"] for row in rows if row["newClass"]]
    return {
        "count": len(rows),
        "newClassCount": len(new_classes),
        "locallySolubleNewClassCount": sum(
            1 for row in rows if row["newClass"] and row["locallySoluble"]
        ),
        "newClasses": new_classes,
        "records": rows[:50],
        "truncated": len(rows) > 50,
    }


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
    selmer_order = _first_int(SELMER_ORDER_RE.pattern, output)
    sha_bound_match = SHA_TWO_BOUND_RE.search(output)
    sha_two_bound_order = int(sha_bound_match.group("order")) if sha_bound_match else None
    sha_two_bound_operator = sha_bound_match.group("op") if sha_bound_match else None
    rank_interval = _rank_interval(output)
    quartics = _parse_type3_quartics(output)

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
        "rankInterval": rank_interval,
        "selmerOrder": selmer_order,
        "shaTwoBoundOrder": sha_two_bound_order,
        "shaTwoBoundOperator": sha_two_bound_operator,
        "type3Quartics": quartics,
        "status": status,
    }


def _expected_structure_order(structure: str | None) -> int | None:
    if not structure:
        return None
    factors = [int(value) for value in re.findall(r"\b(?:Z|C)\s*(?:/|_)\s*(\d+)\b", structure, re.IGNORECASE)]
    return prod(factors) if factors else None


def _visible_sha_two_order(
    mwrank_trace: dict | None,
    two_selmer_rank: int | None,
    torsion_two_primary_order: int | None,
) -> int | None:
    trace = mwrank_trace or {}
    sha_info = trace.get("shaTwoInformation") if isinstance(trace.get("shaTwoInformation"), dict) else {}
    exact = _int_or_none(sha_info.get("shaE_two"))
    if exact is not None:
        return exact
    bound = _int_or_none(trace.get("shaTwoBoundOrder"))
    if bound is not None:
        return bound
    if two_selmer_rank is not None:
        torsion = torsion_two_primary_order or 1
        order = 2**int(two_selmer_rank)
        if order % torsion == 0:
            return order // torsion
    return None


def higher_two_descent_certificate(
    label: str,
    *,
    expected_order: int | None = None,
    expected_structure: str | None = None,
    mwrank_trace: dict | None = None,
    higher_two_transcript: str | None = None,
    two_selmer_rank: int | None = None,
    rank_interval: list[int] | None = None,
    torsion_order: int | None = None,
    source: str | None = None,
) -> dict:
    """Classify higher 2-primary evidence without overclaiming.

    Ordinary 2-descent evidence can show the visible Sha[2] order.  It does not
    prove a higher 2-primary structure such as Z/4 + Z/4 unless an explicit
    higher-two transcript/group computation is supplied.
    """

    transcript_evidence = None
    if higher_two_transcript:
        transcript_evidence = higher_two_power_evidence(
            label,
            higher_two_transcript,
            expected_structure=expected_structure,
            expected_order=expected_order,
            source=source,
            computation_kind="higher_two_descent_certificate_transcript",
        )

    expected = expected_order or _expected_structure_order(expected_structure)
    torsion_two = _two_primary_part(torsion_order) or 1
    trace = mwrank_trace or {}
    trace_rank_interval = trace.get("rankInterval") if isinstance(trace.get("rankInterval"), list) else None
    effective_rank_interval = rank_interval or trace_rank_interval
    visible = _visible_sha_two_order(trace, two_selmer_rank, torsion_two)
    missing_factor = None
    if expected and visible and expected % visible == 0:
        missing_factor = expected // visible

    certified = False
    certification_state = "requires_higher_two_power_evidence"
    status = "higher_two_power_unavailable"
    reason = "no ordinary or higher 2-primary evidence was supplied"

    if transcript_evidence:
        if transcript_evidence.get("status") == "higher_two_power_match":
            certified = True
            certification_state = "certified"
            status = "higher_two_power_certified"
            reason = "explicit higher 2-primary group evidence matches the expected order/structure"
        elif transcript_evidence.get("higherTwoPowerDetected"):
            certification_state = "detected_not_certified"
            status = "higher_two_power_detected_not_certified"
            reason = "higher 2-primary group evidence was detected but did not match the expected target"
        else:
            certification_state = "mismatch"
            status = "higher_two_power_mismatch"
            reason = "explicit transcript did not prove the expected higher 2-primary structure"
    elif expected and visible:
        if visible == expected:
            certified = True
            certification_state = "certified"
            status = "higher_two_power_certified"
            reason = "ordinary 2-primary evidence already matches the expected 2-primary order"
        elif visible < expected:
            certification_state = "requires_higher_two_power_evidence"
            status = "ordinary_two_selmer_gap"
            reason = (
                f"ordinary 2-descent accounts for visible Sha[2] order {visible}, "
                f"but expected 2-primary order is {expected}"
            )
        else:
            certification_state = "mismatch"
            status = "higher_two_power_mismatch"
            reason = (
                f"visible Sha[2] order {visible} is incompatible with expected "
                f"2-primary order {expected}"
            )
    elif effective_rank_interval and effective_rank_interval[0] != effective_rank_interval[1]:
        certification_state = "open_rank_interval"
        status = "mwrank_rank_interval_open"
        reason = "mwrank did not close the rank interval, so higher 2-primary certification is unavailable"

    return {
        "label": label,
        "kind": "higher_two_descent_certificate",
        "engine": "opendescent-native",
        "computed": certified,
        "certified": certified,
        "certificationState": certification_state,
        "status": status,
        "reason": reason,
        "expectedTwoPrimaryOrder": expected,
        "expectedTwoPrimaryStructure": expected_structure,
        "visibleShaTwoOrder": visible,
        "shaTwoOrder": visible if certified and visible == expected else None,
        "missingTwoPowerFactor": missing_factor,
        "rankInterval": effective_rank_interval,
        "rankCertified": (
            effective_rank_interval[0] == effective_rank_interval[1]
            if effective_rank_interval and len(effective_rank_interval) == 2
            else None
        ),
        "twoSelmerRank": two_selmer_rank,
        "torsionTwoPrimaryOrder": torsion_two,
        "mwrankTrace": trace,
        "higherTwoPowerEvidence": transcript_evidence,
    }
