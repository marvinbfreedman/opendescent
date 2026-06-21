"""Certificate generation."""

from __future__ import annotations

import re
from pathlib import Path

from .backends import available_backends, run_backend
from .calculator import CasselsPairing, FiveCoverings, FiveSelmerGroup
from .curve import EllipticCurve
from .finite_field import ap, primes_upto
from .local import bad_primes, reduction_record
from .selmer import two_selmer_certificate
from .transcripts import higher_two_power_evidence, three_selmer_evidence


CASE_METADATA_FIELDS = (
    "prime",
    "expectedSelmerOrder",
    "targetPrimaryOrder",
    "predictedShaOrder",
    "predictedShaFactorization",
    "expectedTwoPrimaryStructure",
    "expectedTwoPrimaryOrder",
    "requiresHigherTwoPowerEvidence",
    "expectedFiveSelmerOrder",
    "expectedFiveSelmerStructure",
    "requiresFiveSelmerEvidence",
    "source",
)


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
        "regulator": row.get("regulator"),
        "generators": row.get("generators"),
        "higherTwoDescent": row.get("higherTwoDescent"),
        "casselsPairing": row.get("casselsPairing"),
        "rankSource": row.get("rankSource"),
        "selmerSource": row.get("selmerSource"),
        "selmerError": row.get("selmerError"),
        "status": "certified rank interval" if certified else "open rank interval",
    }
    return cert


def add_case_metadata(cert: dict, row: dict) -> None:
    metadata = {field: row[field] for field in CASE_METADATA_FIELDS if field in row}
    if metadata:
        cert["caseMetadata"] = metadata


def add_transcript_evidence(cert: dict, row: dict, base_dir: Path) -> None:
    transcript_path = row.get("threeSelmerTranscript") or row.get("transcriptPath")
    if not transcript_path:
        return
    path = Path(transcript_path)
    if not path.is_absolute():
        path = base_dir / path
    try:
        raw = path.read_text()
    except Exception as exc:
        cert["threeSelmerEvidence"] = {
            "label": cert["label"],
            "kind": "magma_three_selmer_transcript",
            "source": str(path),
            "conditional": bool(row.get("grh")),
            "status": "transcript_read_failed",
            "error": str(exc),
        }
        return
    cert["threeSelmerEvidence"] = three_selmer_evidence(
        cert["label"],
        raw,
        row.get("expectedSelmerOrder"),
        grh=bool(row.get("grh")),
        source=str(transcript_path),
    )


def requires_higher_two_power_evidence(row: dict) -> bool:
    if row.get("requiresHigherTwoPowerEvidence"):
        return True
    if row.get("expectedTwoPrimaryStructure") or row.get("expectedTwoPrimaryOrder"):
        return True
    if row.get("higherTwoPowerTranscript") or row.get("twoPrimaryTranscript"):
        return True
    factorization = str(row.get("predictedShaFactorization") or "")
    if re.search(r"(^|[^0-9])2\^([2-9]|\d{2,})", factorization):
        return True
    try:
        target_order = int(row.get("targetPrimaryOrder") or 1)
    except Exception:
        target_order = 1
    return row.get("prime") == 2 and target_order > 2


def missing_higher_two_power_evidence(cert: dict, row: dict, reason: str) -> dict:
    return {
        "label": cert["label"],
        "kind": "higher_two_power_requirement",
        "required": True,
        "source": row.get("higherTwoPowerTranscript") or row.get("twoPrimaryTranscript"),
        "expectedStructure": row.get("expectedTwoPrimaryStructure"),
        "expectedOrder": row.get("expectedTwoPrimaryOrder"),
        "status": "missing_higher_two_power_evidence",
        "reason": reason,
    }


def requires_five_selmer_evidence(row: dict) -> bool:
    if row.get("requiresFiveSelmerEvidence"):
        return True
    if row.get("fiveSelmerTranscript") or row.get("expectedFiveSelmerOrder"):
        return True
    if row.get("expectedFiveSelmerStructure"):
        return True
    try:
        target_order = int(row.get("targetPrimaryOrder") or 1)
    except Exception:
        target_order = 1
    return row.get("prime") == 5 and target_order > 1


def missing_five_selmer_evidence(cert: dict, row: dict, reason: str) -> dict:
    return {
        "label": cert["label"],
        "kind": "five_selmer_group_requirement",
        "function": "FiveSelmerGroup(E)",
        "prime": 5,
        "required": True,
        "source": row.get("fiveSelmerTranscript"),
        "expectedStructure": row.get("expectedFiveSelmerStructure"),
        "expectedOrder": row.get("expectedFiveSelmerOrder"),
        "status": "missing_five_selmer_evidence",
        "reason": reason,
    }


def add_five_selmer_evidence(cert: dict, curve: EllipticCurve, row: dict, base_dir: Path, evidence_transcripts: bool) -> None:
    required = requires_five_selmer_evidence(row)
    transcript_path = row.get("fiveSelmerTranscript")
    if not required and not transcript_path:
        return
    if not evidence_transcripts:
        cert["fiveSelmerEvidence"] = missing_five_selmer_evidence(
            cert,
            row,
            "transcript evidence was not loaded; rerun with --evidence-transcripts",
        )
        return
    if not transcript_path:
        cert["fiveSelmerEvidence"] = missing_five_selmer_evidence(
            cert,
            row,
            "no fiveSelmerTranscript was supplied",
        )
        return

    path = Path(transcript_path)
    if not path.is_absolute():
        path = base_dir / path
    try:
        raw = path.read_text()
    except Exception as exc:
        cert["fiveSelmerEvidence"] = missing_five_selmer_evidence(
            cert,
            row,
            f"transcript_read_failed: {exc}",
        )
        return
    cert["fiveSelmerEvidence"] = FiveSelmerGroup(
        curve,
        transcript=raw,
        expected_order=row.get("expectedFiveSelmerOrder"),
        expected_structure=row.get("expectedFiveSelmerStructure"),
        grh=bool(row.get("grh") or row.get("fiveSelmerGRH")),
        source=str(transcript_path),
    )


def add_higher_two_power_evidence(cert: dict, row: dict, base_dir: Path, evidence_transcripts: bool) -> None:
    required = requires_higher_two_power_evidence(row)
    transcript_path = row.get("higherTwoPowerTranscript") or row.get("twoPrimaryTranscript")
    if not required and not transcript_path:
        return
    if not evidence_transcripts:
        cert["higherTwoPowerEvidence"] = missing_higher_two_power_evidence(
            cert,
            row,
            "transcript evidence was not loaded; rerun with --evidence-transcripts",
        )
        return
    if not transcript_path:
        cert["higherTwoPowerEvidence"] = missing_higher_two_power_evidence(
            cert,
            row,
            "no higherTwoPowerTranscript or twoPrimaryTranscript was supplied",
        )
        return

    path = Path(transcript_path)
    if not path.is_absolute():
        path = base_dir / path
    try:
        raw = path.read_text()
    except Exception as exc:
        cert["higherTwoPowerEvidence"] = missing_higher_two_power_evidence(
            cert,
            row,
            f"transcript_read_failed: {exc}",
        )
        return
    cert["higherTwoPowerEvidence"] = higher_two_power_evidence(
        cert["label"],
        raw,
        expected_structure=row.get("expectedTwoPrimaryStructure"),
        expected_order=row.get("expectedTwoPrimaryOrder"),
        grh=bool(row.get("grh")),
        source=str(transcript_path),
        computation_kind=row.get("higherTwoPowerComputationKind"),
    )


def native_status_block(cert: dict) -> dict:
    statuses = {}
    for key in ("fiveDescent", "fiveCoverings", "casselsPairing"):
        if key in cert:
            statuses[key] = {
                "computed": cert[key].get("computed"),
                "status": cert[key].get("status"),
            }
    complete = bool(statuses) and all(row.get("computed") is True for row in statuses.values())
    return {
        "engine": "opendescent-native",
        "complete": complete,
        "statuses": statuses,
    }


def add_native_descent_tasks(
    cert: dict,
    curve: EllipticCurve,
    point_bound: int,
    five_descent: bool,
    cassels_pairing: bool,
) -> None:
    if five_descent:
        cert["fiveDescent"] = FiveSelmerGroup(curve, mode="native", search_bound=point_bound)
        cert["fiveCoverings"] = FiveCoverings(curve, search_bound=point_bound)
    if cassels_pairing:
        coverings = cert.get("fiveCoverings", {}).get("coverings", [])
        cert["casselsPairing"] = CasselsPairing(curve, coverings, prime=5)
    if five_descent or cassels_pairing:
        cert["nativeComputationStatus"] = native_status_block(cert)


def build_certificate(
    payload: dict,
    point_bound: int = 50,
    prime_bound: int = 31,
    backend: str = "native",
    input_path: str | None = None,
    evidence_transcripts: bool = False,
    five_descent: bool = False,
    cassels_pairing: bool = False,
    native_descent_tasks: bool = False,
) -> dict:
    backend_result = run_backend(backend, input_path)
    backend_rows = {}
    parsed = backend_result.get("parsed") if backend_result else None
    if isinstance(parsed, dict) and isinstance(parsed.get("curves"), dict):
        backend_rows = parsed["curves"]

    curves = []
    base_dir = Path(input_path).resolve().parent if input_path else Path.cwd()
    for row in payload.get("curves", []):
        curve = EllipticCurve.from_weierstrass(
            row["weierstrass"],
            label=row.get("label", "curve"),
            conductor=row.get("conductor"),
        )
        cert = curve_certificate(curve, point_bound=point_bound, prime_bound=prime_bound)
        cert = merge_backend(cert, backend_rows)
        add_case_metadata(cert, row)
        if evidence_transcripts:
            add_transcript_evidence(cert, row, base_dir)
        add_five_selmer_evidence(cert, curve, row, base_dir, evidence_transcripts)
        add_higher_two_power_evidence(cert, row, base_dir, evidence_transcripts)
        run_five = five_descent or native_descent_tasks
        run_cassels = cassels_pairing or native_descent_tasks
        add_native_descent_tasks(cert, curve, point_bound, run_five, run_cassels)
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
            "higher 2-descent or Cassels pairing closure when Selmer rank exceeds rank lower bound",
            "native 5-Selmer descent for FiveSelmerGroup(E)",
            "degree-5 genus-one covering construction",
            "local solubility for 5-coverings",
            "native Cassels pairing entries for 5-coverings",
            "Mordell-Weil rank certificate",
        ],
    }
