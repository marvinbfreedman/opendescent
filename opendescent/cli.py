"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .certificate import build_certificate


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate OpenDescent JSON certificates.")
    parser.add_argument("input", help="Input JSON containing curves.")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout.")
    parser.add_argument("--point-bound", type=int, default=50)
    parser.add_argument("--prime-bound", type=int, default=31)
    parser.add_argument(
        "--backend",
        choices=["native", "sage"],
        default="native",
        help="Optional open-source backend for rank/Selmer certification.",
    )
    args = parser.parse_args()

    input_path = str(Path(args.input).resolve())
    payload = json.loads(Path(input_path).read_text())
    cert = build_certificate(
        payload,
        point_bound=args.point_bound,
        prime_bound=args.prime_bound,
        backend=args.backend,
        input_path=input_path,
    )
    text = json.dumps(cert, indent=2, sort_keys=True) + "\n"
    if args.out == "-":
        print(text, end="")
    else:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
