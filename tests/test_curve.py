import json
from pathlib import Path
from fractions import Fraction
from tempfile import TemporaryDirectory

from opendescent.backends import available_backends, run_backend
from opendescent.calculator import FiveSelmerGroup
from opendescent.certificate import build_certificate
from opendescent.curve import EllipticCurve, Point
from opendescent.finite_field import ap, count_points_mod_p
from opendescent.local import reduction_record
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
    evidence = FiveSelmerGroup(curve)
    assert evidence["computed"] is False
    assert evidence["available"] is False
    assert evidence["status"] == "unavailable"


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
