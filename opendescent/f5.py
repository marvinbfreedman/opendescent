"""Small linear algebra helpers over finite fields."""

from __future__ import annotations


def mod_inv(value: int, p: int) -> int:
    value %= p
    if value == 0:
        raise ZeroDivisionError("zero has no inverse modulo p")
    return pow(value, -1, p)


def normalize_matrix(matrix: list[list[int]], p: int) -> list[list[int]]:
    if p <= 1:
        raise ValueError("p must be prime")
    if not matrix:
        return []
    width = len(matrix[0])
    for row in matrix:
        if len(row) != width:
            raise ValueError("matrix rows must have the same length")
    return [[int(entry) % p for entry in row] for row in matrix]


def rref_mod(matrix: list[list[int]], p: int) -> tuple[list[list[int]], list[int]]:
    rows = normalize_matrix(matrix, p)
    if not rows:
        return [], []
    height = len(rows)
    width = len(rows[0])
    pivot_columns: list[int] = []
    pivot_row = 0

    for col in range(width):
        pivot = None
        for row in range(pivot_row, height):
            if rows[row][col] % p:
                pivot = row
                break
        if pivot is None:
            continue
        rows[pivot_row], rows[pivot] = rows[pivot], rows[pivot_row]
        inv = mod_inv(rows[pivot_row][col], p)
        rows[pivot_row] = [(entry * inv) % p for entry in rows[pivot_row]]
        for row in range(height):
            if row == pivot_row:
                continue
            factor = rows[row][col] % p
            if factor:
                rows[row] = [
                    (rows[row][idx] - factor * rows[pivot_row][idx]) % p
                    for idx in range(width)
                ]
        pivot_columns.append(col)
        pivot_row += 1
        if pivot_row == height:
            break

    return rows, pivot_columns


def rank_mod(matrix: list[list[int]], p: int) -> int:
    _, pivots = rref_mod(matrix, p)
    return len(pivots)


def nullspace_mod(matrix: list[list[int]], p: int) -> list[list[int]]:
    rows = normalize_matrix(matrix, p)
    if not rows:
        return []
    rref, pivots = rref_mod(rows, p)
    width = len(rows[0])
    pivot_set = set(pivots)
    free_columns = [col for col in range(width) if col not in pivot_set]
    basis: list[list[int]] = []

    for free_col in free_columns:
        vec = [0] * width
        vec[free_col] = 1
        for row_idx, pivot_col in enumerate(pivots):
            vec[pivot_col] = (-rref[row_idx][free_col]) % p
        basis.append(vec)
    return basis


def is_square_matrix(matrix: list[list[int]]) -> bool:
    return bool(matrix) and all(len(row) == len(matrix) for row in matrix)


def is_alternating_matrix(matrix: list[list[int]], p: int) -> bool:
    rows = normalize_matrix(matrix, p)
    if not rows:
        return True
    if not is_square_matrix(rows):
        return False
    for i, row in enumerate(rows):
        if row[i] % p != 0:
            return False
        for j in range(i + 1, len(rows)):
            if (rows[i][j] + rows[j][i]) % p != 0:
                return False
    return True
