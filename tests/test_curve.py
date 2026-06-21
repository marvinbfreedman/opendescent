import json
from fractions import Fraction

from opendescent.backends import available_backends, run_backend
from opendescent.certificate import build_certificate
from opendescent.curve import EllipticCurve, Point
from opendescent.finite_field import ap, count_points_mod_p
from opendescent.local import reduction_record
from opendescent.mwrank_backend import parse_mwrank_output


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


def test_unimplemented_backend_returns_json_failure():
    result = run_backend("pari_gp", "examples/calibration_curves.json")
    assert result["succeeded"] is False
    assert result["parsed"] is None
    assert "not implemented" in result["error"]
