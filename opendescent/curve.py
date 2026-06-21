"""Elliptic curves over Q in integral Weierstrass form."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt


@dataclass(frozen=True)
class Point:
    x: Fraction | None
    y: Fraction | None

    @staticmethod
    def infinity() -> "Point":
        return Point(None, None)

    @property
    def is_infinity(self) -> bool:
        return self.x is None or self.y is None

    def as_pair(self) -> list[str] | str:
        if self.is_infinity:
            return "O"
        return [str(self.x), str(self.y)]


@dataclass(frozen=True)
class EllipticCurve:
    a1: int
    a2: int
    a3: int
    a4: int
    a6: int
    label: str = "curve"
    conductor: int | None = None

    @classmethod
    def from_weierstrass(
        cls,
        coeffs: list[int],
        label: str = "curve",
        conductor: int | None = None,
    ) -> "EllipticCurve":
        if len(coeffs) != 5:
            raise ValueError("weierstrass must contain [a1,a2,a3,a4,a6]")
        return cls(*map(int, coeffs), label=label, conductor=conductor)

    @property
    def weierstrass(self) -> list[int]:
        return [self.a1, self.a2, self.a3, self.a4, self.a6]

    def invariants(self) -> dict[str, int | str | None]:
        a1, a2, a3, a4, a6 = self.weierstrass
        b2 = a1 * a1 + 4 * a2
        b4 = 2 * a4 + a1 * a3
        b6 = a3 * a3 + 4 * a6
        b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
        c4 = b2 * b2 - 24 * b4
        c6 = -(b2**3) + 36 * b2 * b4 - 216 * b6
        delta = -(b2**2) * b8 - 8 * (b4**3) - 27 * (b6**2) + 9 * b2 * b4 * b6
        j = None if delta == 0 else Fraction(c4**3, delta)
        return {
            "b2": b2,
            "b4": b4,
            "b6": b6,
            "b8": b8,
            "c4": c4,
            "c6": c6,
            "discriminant": delta,
            "j": None if j is None else str(j),
        }

    def is_on_curve(self, p: Point) -> bool:
        if p.is_infinity:
            return True
        x = Fraction(p.x)
        y = Fraction(p.y)
        lhs = y * y + self.a1 * x * y + self.a3 * y
        rhs = x**3 + self.a2 * x * x + self.a4 * x + self.a6
        return lhs == rhs

    def neg(self, p: Point) -> Point:
        if p.is_infinity:
            return p
        return Point(p.x, -p.y - self.a1 * p.x - self.a3)

    def add(self, p: Point, q: Point) -> Point:
        if p.is_infinity:
            return q
        if q.is_infinity:
            return p
        if q == self.neg(p):
            return Point.infinity()

        x1, y1 = Fraction(p.x), Fraction(p.y)
        x2, y2 = Fraction(q.x), Fraction(q.y)

        if p != q:
            lam = (y2 - y1) / (x2 - x1)
            nu = (y1 * x2 - y2 * x1) / (x2 - x1)
        else:
            denom = 2 * y1 + self.a1 * x1 + self.a3
            if denom == 0:
                return Point.infinity()
            lam = (3 * x1 * x1 + 2 * self.a2 * x1 + self.a4 - self.a1 * y1) / denom
            nu = (-x1**3 + self.a4 * x1 + 2 * self.a6 - self.a3 * y1) / denom

        x3 = lam * lam + self.a1 * lam - self.a2 - x1 - x2
        y3 = -(lam + self.a1) * x3 - nu - self.a3
        out = Point(x3, y3)
        if not self.is_on_curve(out):
            raise ArithmeticError("group law produced point off curve")
        return out

    def mul(self, n: int, p: Point) -> Point:
        if n == 0 or p.is_infinity:
            return Point.infinity()
        if n < 0:
            return self.mul(-n, self.neg(p))
        acc = Point.infinity()
        cur = p
        while n:
            if n & 1:
                acc = self.add(acc, cur)
            cur = self.add(cur, cur)
            n >>= 1
        return acc

    def integral_points(self, bound: int = 50) -> list[Point]:
        points: list[Point] = []
        for x_int in range(-bound, bound + 1):
            # y satisfies y^2 + B y - C = 0.
            b = self.a1 * x_int + self.a3
            c = -(x_int**3 + self.a2 * x_int * x_int + self.a4 * x_int + self.a6)
            disc = b * b - 4 * c
            if disc < 0:
                continue
            root = isqrt(disc)
            if root * root != disc:
                continue
            for numer in (-b + root, -b - root):
                if numer % 2 == 0:
                    p = Point(Fraction(x_int), Fraction(numer // 2))
                    if self.is_on_curve(p) and p not in points:
                        points.append(p)
        return points

