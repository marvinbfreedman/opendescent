from fractions import Fraction

from opendescent.curve import EllipticCurve, Point
from opendescent.finite_field import ap, count_points_mod_p


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

