import json
from pathlib import Path
from fractions import Fraction
from tempfile import TemporaryDirectory

from opendescent.backends import available_backends, run_backend
from opendescent.calculator import CasselsPairing, FiveCoverings, FiveSelmerGroup
from opendescent.certificate import build_certificate
from opendescent.curve import EllipticCurve, Point
from opendescent.f5 import is_alternating_matrix, nullspace_mod, rank_mod, rref_mod
from opendescent.five_descent import FiveCovering, five_descent_prime_set, native_five_descent
from opendescent.finite_field import ap, count_points_mod_p
from opendescent.local import reduction_record
from opendescent.magma_batch_export import (
    P3_REMAINING_CASES,
    P5_PROBE_CASES,
    export_batches,
    render_p3_magma,
    render_p5_magma,
    render_readme,
)
from opendescent.mwrank_backend import parse_mwrank_output
from opendescent.transcripts import (
    higher_two_power_evidence,
    parse_abelian_group_structure,
    parse_selmer_group_order,
    parse_three_selmer_order,
    three_selmer_evidence,
)


def test_11a1_invariants_and_points():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    inv = curve.invariants()
    assert inv["discriminant"] == -161051
    assert inv["c4"] == 496
    p = Point(Fraction(5), Fraction(5))
    assert curve.is_on_curve(p)
    assert curve.add(p, curve.neg(p)).is_infinity


def test_point_count_ap():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    assert count_points_mod_p(curve, 2) == 5
    assert ap(curve, 2) == -2


def test_semistable_bad_prime_record():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    row = reduction_record(curve, 11)
    assert row["reduction"] == "split multiplicative"
    assert row["localFactor"] == [1, 1]


def test_native_certificate_marks_descent_gap():
    payload = {
        "curves": [
            {
                "label": "11a1",
                "conductor": 11,
                "weierstrass": [0, -1, 1, -10, -20],
            }
        ]
    }
    cert = build_certificate(payload)
    assert cert["backend"] == "native"
    assert cert["curves"][0]["descent"]["rankCertified"] is False
    assert cert["curves"][0]["descent"]["rankUpperBound"] is None


def test_backend_registry_shape():
    registry = available_backends()
    assert registry["native"]["available"] is True
    assert "sage" in registry
    assert registry["magma"]["kind"] == "optional licensed external"


def test_f5_linear_algebra_helpers():
    matrix = [[1, 2, 3], [2, 0, 1], [0, 0, 0]]
    rref, pivots = rref_mod(matrix, 5)
    assert pivots == [0, 1]
    assert rank_mod(matrix, 5) == 2
    assert len(nullspace_mod(matrix, 5)) == 1
    assert is_alternating_matrix([[0, 2], [3, 0]], 5)


def test_mwrank_output_parser_closes_rank_interval():
    output = """
Rank = 2
Rank of S^2(E)  = 2
Generator 1 is [0:-1:1]; height 0.3270007736516
Regulator = 0.15246017794314
The rank and full Mordell-Weil basis have been determined unconditionally.
"""
    row = parse_mwrank_output("389a1", 0, output)
    assert row["rankInterval"] == [2, 2]
    assert row["rankCertified"] is True
    assert row["twoSelmerRank"] == 2
    assert row["generators"][0]["point"] == "[0:-1:1]"


def test_mwrank_output_parser_records_higher_two_descent():
    output = """
Using 2-isogenous curve [0,-298,0,-7,0] (minimal model [1,1,0,-1850,-31411])
First step, determining 1st descent Selmer groups
After first local descent, rank bound = 0
rk(S^{phi}(E'))= 1
rk(S^{phi'}(E))= 1
Second step, determining 2nd descent Selmer groups
After second local descent, rank bound = 0
rk(phi'(S^{2}(E)))= 1
rk(phi(S^{2}(E')))= 1
rk(S^{2}(E))= 1
rk(S^{2}(E'))= 1
Information on III(E/Q):
  #III(E/Q)[phi']    = 1
  #III(E/Q)[2]       = 1
Used descent via 2-isogeny with isogenous curve E' = [1,1,0,-1850,-31411]
Rank = 0
Rank of S^2(E)  = 1
The rank and full Mordell-Weil basis have been determined unconditionally.
"""
    row = parse_mwrank_output("2429b1", 0, output)
    higher = row["higherTwoDescent"]
    assert higher["secondDescentDetected"] is True
    assert higher["isogenyDescentDetected"] is True
    assert higher["isogenousCurve"] == "[1,1,0,-1850,-31411]"
    assert higher["selmerDimensions"]["rankBoundAfterSecondDescent"] == 0
    assert higher["selmerDimensions"]["rankS2E"] == 1
    assert higher["shaTwoInformation"]["shaE_two"] == 1
    assert row["casselsPairing"]["computed"] is False


def test_unimplemented_backend_returns_json_failure():
    result = run_backend("pari_gp", "examples/calibration_curves.json")
    assert result["succeeded"] is False
    assert result["parsed"] is None
    assert "not implemented" in result["error"]


def test_three_selmer_transcript_parser_grh_match():
    raw = """
===== 2429b1 GRH =====
0 true
Abelian Group isomorphic to Z/3 + Z/3
Defined on 2 generators
Relations:
    3*G.1 = 0
    3*G.2 = 0
9
"""
    assert parse_three_selmer_order(raw) == 9
    evidence = three_selmer_evidence("2429b1", raw, 9, grh=True, source="fixture.txt")
    assert evidence["conditional"] is True
    assert evidence["matchesExpected"] is True
    assert evidence["status"] == "conditional_match"


def test_higher_two_power_parser_detects_z4_plus_z4():
    raw = """
Higher 2-primary computation
Abelian Group isomorphic to Z/4 + Z/4
Defined on 2 generators
"""
    parsed = parse_abelian_group_structure(raw)
    assert parsed["cyclicFactors"] == [4, 4]
    assert parsed["order"] == 16
    assert parsed["exponent"] == 4
    assert parsed["higherTwoPowerDetected"] is True

    evidence = higher_two_power_evidence(
        "case",
        raw,
        expected_structure="Z/4 + Z/4",
        expected_order=16,
    )
    assert evidence["normalizedStructure"] == "Z/4 + Z/4"
    assert evidence["matchesExpectedStructure"] is True
    assert evidence["matchesExpectedOrder"] is True
    assert evidence["status"] == "higher_two_power_match"


def test_certificate_marks_missing_required_higher_two_power_evidence():
    payload = {
        "curves": [
            {
                "label": "needs-2power",
                "weierstrass": [0, -1, 1, -10, -20],
                "prime": 2,
                "targetPrimaryOrder": 16,
                "expectedTwoPrimaryStructure": "Z/4 + Z/4",
                "requiresHigherTwoPowerEvidence": True,
            }
        ]
    }
    cert = build_certificate(payload)
    evidence = cert["curves"][0]["higherTwoPowerEvidence"]
    assert evidence["required"] is True
    assert evidence["status"] == "missing_higher_two_power_evidence"


def test_certificate_attaches_higher_two_power_transcript():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        transcript = base / "z4_plus_z4.txt"
        transcript.write_text("Abelian Group isomorphic to Z/4 + Z/4\n")
        input_path = base / "input.json"
        payload = {
            "curves": [
                {
                    "label": "has-2power",
                    "weierstrass": [0, -1, 1, -10, -20],
                    "expectedTwoPrimaryStructure": "Z/4 + Z/4",
                    "expectedTwoPrimaryOrder": 16,
                    "higherTwoPowerTranscript": transcript.name,
                }
            ]
        }
        input_path.write_text(json.dumps(payload))

        cert = build_certificate(payload, input_path=str(input_path), evidence_transcripts=True)
        evidence = cert["curves"][0]["higherTwoPowerEvidence"]
        assert evidence["normalizedStructure"] == "Z/4 + Z/4"
        assert evidence["higherTwoPowerDetected"] is True
        assert evidence["matchesExpectedStructure"] is True
        assert evidence["matchesExpectedOrder"] is True
        assert evidence["status"] == "higher_two_power_match"


def test_five_selmer_group_calculator_parses_z5_plus_z5():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    raw = """
FiveSelmerGroup(E)
Abelian Group isomorphic to Z/5 + Z/5
Defined on 2 generators
25
"""
    assert parse_selmer_group_order(raw) == 25
    evidence = FiveSelmerGroup(
        curve,
        transcript=raw,
        expected_structure="Z/5 + Z/5",
        expected_order=25,
    )
    assert evidence["function"] == "FiveSelmerGroup(E)"
    assert evidence["prime"] == 5
    assert evidence["normalizedStructure"] == "Z/5 + Z/5"
    assert evidence["order"] == 25
    assert evidence["primePrimary"] is True
    assert evidence["vectorSpaceDimension"] == 2
    assert evidence["status"] == "selmer_group_match"


def test_five_selmer_group_calculator_marks_unavailable_without_transcript():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    evidence = FiveSelmerGroup(curve, mode="transcript")
    assert evidence["computed"] is False
    assert evidence["available"] is False
    assert evidence["status"] == "unavailable"


def test_native_five_descent_task_is_partial_and_auditable():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    result = FiveSelmerGroup(curve, mode="native", search_bound=10)
    assert result["kind"] == "native_five_descent"
    assert result["source"] == "native"
    assert result["computed"] is False
    assert 5 in result["task"]["localPrimes"]
    assert "construct degree-5 genus-one normal curve representatives" in result["missingSteps"]
    assert five_descent_prime_set(curve) == result["task"]["localPrimes"]
    assert native_five_descent(curve, search_bound=10).to_json()["status"] == result["status"]


def test_native_five_coverings_task_is_partial():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    result = FiveCoverings(curve, search_bound=10)
    assert result["kind"] == "native_five_coverings"
    assert result["computed"] is False
    assert result["coverings"] == []


def test_cassels_pairing_computes_supplied_five_covering_matrix():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    coverings = [
        FiveCovering(label="A", cassels_values={"B": 2}).to_json(),
        FiveCovering(label="B").to_json(),
    ]
    result = CasselsPairing(curve, coverings, prime=5)
    assert result["computed"] is True
    assert result["matrix"] == [[0, 2], [3, 0]]
    assert result["alternating"] is True
    assert result["rank"] == 2
    assert result["radicalDimension"] == 0


def test_cassels_pairing_marks_missing_entries():
    curve = EllipticCurve.from_weierstrass([0, -1, 1, -10, -20], label="11a1")
    coverings = [FiveCovering(label="A").to_json(), FiveCovering(label="B").to_json()]
    result = CasselsPairing(curve, coverings, prime=5)
    assert result["computed"] is False
    assert result["status"].startswith("partial")
    assert result["missingEntries"] == [["A", "B"]]


def test_certificate_attaches_five_selmer_transcript():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        transcript = base / "five_selmer.txt"
        transcript.write_text("Abelian Group isomorphic to Z/5 + Z/5\n25\n")
        input_path = base / "input.json"
        payload = {
            "curves": [
                {
                    "label": "has-five",
                    "weierstrass": [0, -1, 1, -10, -20],
                    "prime": 5,
                    "expectedFiveSelmerStructure": "Z/5 + Z/5",
                    "expectedFiveSelmerOrder": 25,
                    "fiveSelmerTranscript": transcript.name,
                }
            ]
        }
        input_path.write_text(json.dumps(payload))

        cert = build_certificate(payload, input_path=str(input_path), evidence_transcripts=True)
        evidence = cert["curves"][0]["fiveSelmerEvidence"]
        assert evidence["function"] == "FiveSelmerGroup(E)"
        assert evidence["normalizedStructure"] == "Z/5 + Z/5"
        assert evidence["matchesExpectedStructure"] is True
        assert evidence["matchesExpectedOrder"] is True


def test_certificate_marks_missing_required_five_selmer_evidence():
    payload = {
        "curves": [
            {
                "label": "needs-five",
                "weierstrass": [0, -1, 1, -10, -20],
                "prime": 5,
                "targetPrimaryOrder": 25,
                "requiresFiveSelmerEvidence": True,
            }
        ]
    }
    cert = build_certificate(payload)
    evidence = cert["curves"][0]["fiveSelmerEvidence"]
    assert evidence["function"] == "FiveSelmerGroup(E)"
    assert evidence["required"] is True
    assert evidence["status"] == "missing_five_selmer_evidence"


def test_certificate_attaches_native_descent_tasks():
    payload = {
        "curves": [
            {
                "label": "native-tasks",
                "weierstrass": [0, -1, 1, -10, -20],
            }
        ]
    }
    cert = build_certificate(payload, native_descent_tasks=True, point_bound=10)
    curve = cert["curves"][0]
    assert curve["fiveDescent"]["kind"] == "native_five_descent"
    assert curve["fiveCoverings"]["kind"] == "native_five_coverings"
    assert curve["casselsPairing"]["kind"] == "cassels_pairing"
    assert curve["nativeComputationStatus"]["complete"] is False


def test_magma_batch_export_renders_expected_case_sets():
    assert [case.label for case in P3_REMAINING_CASES] == [
        "2429b1",
        "2534e1",
        "2534f1",
        "2674b1",
        "2849a1",
    ]
    assert [case.label for case in P5_PROBE_CASES] == [
        "1664k1",
        "2366f1",
        "2574d1",
        "2834d1",
        "2900d1",
    ]

    p3 = render_p3_magma(P3_REMAINING_CASES)
    assert p3.count("ThreeSelmerGroup(E)") == 5
    assert 'SetClassGroupBounds("GRH")' in p3
    assert not any(line.strip() == 'SetClassGroupBounds("GRH");' for line in p3.splitlines())
    assert "===== 2534e1 p=3 unconditional =====" in p3
    assert "expectedSelmer=9" in p3

    p5 = render_p5_magma(P5_PROBE_CASES)
    assert p5.count("FiveSelmerGroup") >= 10
    assert "SelmerGroup(5, E)" in p5
    assert "SelmerGroup(E, 5)" in p5
    assert "===== 2900d1 p=5 probe =====" in p5


def test_magma_batch_export_writes_requested_files():
    with TemporaryDirectory() as tmp:
        outputs = export_batches(Path(tmp), P3_REMAINING_CASES, P5_PROBE_CASES)
        assert sorted(outputs) == [
            "bsd_local_magma_p3_remaining.m",
            "bsd_local_magma_p5_probe.m",
            "bsd_local_magma_readme.md",
        ]
        for path in outputs.values():
            assert path.exists()
        readme = outputs["bsd_local_magma_readme.md"].read_text()
        assert "magma -b bsd_local_magma_p3_remaining.m" in readme
        assert "bsd_record_magma_three_selmer.py --label 2429b1" in readme
        assert "fiveSelmerTranscript" in readme
        assert "Order(G) = 9" in readme
