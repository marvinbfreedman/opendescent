"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backends import BACKENDS, available_backends
from .certificate import build_certificate


def print_summary(cert: dict) -> None:
    print(f"status={cert['status']}")
    print(f"backend={cert['backend']}")
    for curve in cert["curves"]:
        descent = curve["descent"]
        line = (
            f"{curve['label']}: "
            f"rankInterval={descent.get('rankInterval')} "
            f"certified={descent.get('rankCertified')} "
            f"selmer={descent.get('twoSelmerRank')} "
            f"torsion={descent.get('torsionOrder')} "
            f"engine={descent.get('engine')}"
        )
        higher = descent.get("higherTwoDescent") or {}
        if higher.get("secondDescentDetected"):
            line += " higher2=second-descent"
        elif higher.get("method"):
            line += f" descentMethod={higher.get('method')}"
        cassels = descent.get("casselsPairing") or {}
        if cassels.get("computed"):
            line += " casselsPairing=computed"
        two_power = curve.get("higherTwoPowerEvidence")
        if two_power:
            line += (
                f" higher2Power={two_power.get('normalizedStructure') or two_power.get('status')}"
                f" higher2PowerStatus={two_power.get('status')}"
            )
        five = curve.get("fiveSelmerEvidence")
        if five:
            line += (
                f" fiveSelmer={five.get('normalizedStructure') or five.get('order') or five.get('status')}"
                f" fiveSelmerStatus={five.get('status')}"
            )
        evidence = curve.get("threeSelmerEvidence")
        if evidence:
            line += (
                f" threeSelmerOrder={evidence.get('threeSelmerOrder')}"
                f" evidenceMatch={evidence.get('matchesExpected')}"
                f" conditional={evidence.get('conditional')}"
            )
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate OpenDescent JSON certificates.")
    parser.add_argument("input", nargs="?", help="Input JSON containing curves.")
    parser.add_argument("--out", default="-", help="Output JSON path, or '-' for stdout.")
    parser.add_argument("--point-bound", type=int, default=50)
    parser.add_argument("--prime-bound", type=int, default=31)
    parser.add_argument("--list-backends", action="store_true", help="Print backend availability and exit.")
    parser.add_argument("--quiet", action="store_true", help="Suppress concise summary when writing to a file.")
    parser.add_argument("--summary-only", action="store_true", help="Print only the concise certificate summary.")
    parser.add_argument("--evidence-transcripts", action="store_true", help="Attach transcript evidence referenced by input curves.")
    parser.add_argument(
        "--backend",
        choices=BACKENDS,
        default="native",
        help="Optional open-source backend for rank/Selmer certification.",
    )
    args = parser.parse_args()

    if args.list_backends:
        print(json.dumps(available_backends(), indent=2, sort_keys=True))
        return
    if not args.input:
        parser.error("input is required unless --list-backends is used")

    input_path = str(Path(args.input).resolve())
    payload = json.loads(Path(input_path).read_text())
    cert = build_certificate(
        payload,
        point_bound=args.point_bound,
        prime_bound=args.prime_bound,
        backend=args.backend,
        input_path=input_path,
        evidence_transcripts=args.evidence_transcripts,
    )
    text = json.dumps(cert, indent=2, sort_keys=True) + "\n"
    if args.summary_only:
        if args.out != "-":
            Path(args.out).write_text(text)
            print(f"wrote {args.out}")
        print_summary(cert)
        return
    if args.out == "-":
        print(text, end="")
    else:
        Path(args.out).write_text(text)
        print(f"wrote {args.out}")
        if not args.quiet:
            print_summary(cert)


if __name__ == "__main__":
    main()
