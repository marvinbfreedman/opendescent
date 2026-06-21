"""codex-2 higher 2-descent certificate exporter."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .codex2_no_magma import discover_codex2_dir
from .higher_descent import higher_two_descent_certificate
from .mwrank_backend import parse_mwrank_output


HIGHER2_OUT = "codex2_higher2_certificate.json"
SUMMARY_OUT = "codex2_higher2_summary.md"
UNRESOLVED_OUT = "codex2_higher2_unresolved.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def load_higher2_cases(codex2_dir: Path, unresolved_path: Path | None = None) -> list[dict]:
    cases: dict[str, dict] = {}
    audit_path = codex2_dir / "bsd_2primary_audit.json"
    if audit_path.exists():
        for row in _load_json(audit_path).get("rows", []):
            cases[row["label"]] = {
                "label": row["label"],
                "conductor": row.get("conductor"),
                "weierstrass": [int(value) for value in row["aInvariants"]],
                "prime": 2,
                "expectedTwoPrimaryOrder": _int_or_none(row.get("bsd", {}).get("predictedSha2PrimaryOrder")),
                "expectedTwoPrimaryStructure": row.get("expectedTwoPrimaryStructure"),
                "twoSelmerRank": _int_or_none(row.get("twoSelmer", {}).get("dimensionOverF2")),
                "visibleShaTwoOrder": _int_or_none(row.get("twoSelmer", {}).get("sha2OrderAfterTorsion")),
                "torsionOrder": _int_or_none(row.get("torsion", {}).get("order")),
                "sourceArtifact": "bsd_2primary_audit:rows",
            }

    if unresolved_path and unresolved_path.exists():
        unresolved = _load_json(unresolved_path)
        for row in unresolved.get("cases", []):
            if int(row.get("prime", 0)) != 2:
                continue
            existing = cases.get(row["label"], {})
            evidence = row.get("evidence", {})
            cases[row["label"]] = {
                "label": row["label"],
                "conductor": row.get("conductor") or existing.get("conductor"),
                "weierstrass": row.get("weierstrass") or existing.get("weierstrass"),
                "prime": 2,
                "expectedTwoPrimaryOrder": (
                    _int_or_none(row.get("expectedPrimaryOrder"))
                    or existing.get("expectedTwoPrimaryOrder")
                ),
                "expectedTwoPrimaryStructure": existing.get("expectedTwoPrimaryStructure"),
                "twoSelmerRank": existing.get("twoSelmerRank"),
                "visibleShaTwoOrder": existing.get("visibleShaTwoOrder"),
                "torsionOrder": existing.get("torsionOrder"),
                "sourceArtifact": (
                    existing.get("sourceArtifact", "")
                    + ", codex2_no_magma_unresolved:cases"
                ).strip(", "),
                "noMagmaEvidence": evidence,
            }

    return sorted(cases.values(), key=lambda case: (case.get("conductor") or 0, case["label"]))


def run_mwrank_case(case: dict, timeout: int) -> dict:
    if shutil.which("mwrank") is None:
        certificate = higher_two_descent_certificate(
            case["label"],
            expected_order=case.get("expectedTwoPrimaryOrder"),
            expected_structure=case.get("expectedTwoPrimaryStructure"),
            two_selmer_rank=case.get("twoSelmerRank"),
            torsion_order=case.get("torsionOrder"),
        )
        certificate["status"] = "higher_two_power_unavailable"
        certificate["reason"] = "mwrank executable not found in PATH"
        return {
            "case": case,
            "returncode": None,
            "timedOut": False,
            "rawOutput": "",
            "mwrankParsed": None,
            "certificate": certificate,
        }

    curve_text = "[" + ",".join(str(int(value)) for value in case["weierstrass"]) + "]\n"
    try:
        proc = subprocess.run(
            ["mwrank"],
            input=curve_text,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
        raw = proc.stdout + proc.stderr
        parsed = parse_mwrank_output(case["label"], proc.returncode, raw)
        trace = parsed.get("higherTwoDescent")
        rank_interval = parsed.get("rankInterval") or (trace or {}).get("rankInterval")
        two_selmer_rank = parsed.get("twoSelmerRank") or case.get("twoSelmerRank")
        certificate = higher_two_descent_certificate(
            case["label"],
            expected_order=case.get("expectedTwoPrimaryOrder"),
            expected_structure=case.get("expectedTwoPrimaryStructure"),
            mwrank_trace=trace,
            two_selmer_rank=two_selmer_rank,
            rank_interval=rank_interval,
            torsion_order=case.get("torsionOrder"),
        )
        return {
            "case": case,
            "returncode": proc.returncode,
            "timedOut": False,
            "rawOutput": raw,
            "mwrankParsed": parsed,
            "certificate": certificate,
        }
    except subprocess.TimeoutExpired as exc:
        raw = _text(exc.stdout) + _text(exc.stderr)
        certificate = higher_two_descent_certificate(
            case["label"],
            expected_order=case.get("expectedTwoPrimaryOrder"),
            expected_structure=case.get("expectedTwoPrimaryStructure"),
            two_selmer_rank=case.get("twoSelmerRank"),
            torsion_order=case.get("torsionOrder"),
        )
        certificate["status"] = "higher_two_power_unavailable"
        certificate["certificationState"] = "timeout"
        certificate["reason"] = f"mwrank timed out after {timeout} seconds"
        return {
            "case": case,
            "returncode": None,
            "timedOut": True,
            "rawOutput": raw,
            "mwrankParsed": None,
            "certificate": certificate,
        }


def build_report(codex2_dir: Path, unresolved_path: Path | None, timeout: int) -> dict:
    results = []
    for case in load_higher2_cases(codex2_dir, unresolved_path):
        print(f"running {case['label']} higher-2 mwrank...", flush=True)
        result = run_mwrank_case(case, timeout)
        cert = result["certificate"]
        print(
            f"finished {case['label']}: {cert.get('certificationState')} / {cert.get('status')}",
            flush=True,
        )
        results.append(result)

    statuses = Counter(result["certificate"]["status"] for result in results)
    certified = [result["case"]["label"] for result in results if result["certificate"].get("certified")]
    unresolved = [result["case"]["label"] for result in results if not result["certificate"].get("certified")]
    return {
        "artifact": "codex2_higher2_certificate",
        "policy": "no_magma",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "codex2Dir": str(codex2_dir),
        "timeoutSecondsPerCase": timeout,
        "summary": {
            "totalCases": len(results),
            "certifiedCases": len(certified),
            "unresolvedCases": len(unresolved),
            "certifiedLabels": certified,
            "unresolvedLabels": unresolved,
            "statusCounts": dict(sorted(statuses.items())),
        },
        "results": results,
    }


def unresolved_report(report: dict) -> dict:
    results = [result for result in report["results"] if not result["certificate"].get("certified")]
    statuses = Counter(result["certificate"]["status"] for result in results)
    return {
        "artifact": "codex2_higher2_unresolved",
        "policy": "no_magma",
        "sourceArtifact": HIGHER2_OUT,
        "summary": {
            "totalCases": len(results),
            "statusCounts": dict(sorted(statuses.items())),
            "unresolvedLabels": [result["case"]["label"] for result in results],
        },
        "results": results,
    }


def render_markdown(report: dict) -> str:
    rows = []
    unresolved = []
    for result in report["results"]:
        case = result["case"]
        cert = result["certificate"]
        rows.append(
            "| `{label}` | {expected} | {visible} | `{state}` | `{status}` | {missing} |".format(
                label=case["label"],
                expected=cert.get("expectedTwoPrimaryOrder"),
                visible=cert.get("visibleShaTwoOrder"),
                state=cert.get("certificationState"),
                status=cert.get("status"),
                missing=cert.get("missingTwoPowerFactor") or "",
            )
        )
        if not cert.get("certified"):
            unresolved.append(f"- `{case['label']}`: {cert.get('reason')}")

    summary = report["summary"]
    return "\n".join(
        [
            "# codex-2 Higher 2-Descent Summary",
            "",
            "This report records mwrank/open-source 2-descent evidence.  Ordinary",
            "Sha[2] data is not treated as proof of higher 2-primary structure.",
            "",
            "## Summary",
            "",
            f"- total cases: `{summary['totalCases']}`",
            f"- certified cases: `{summary['certifiedCases']}`",
            f"- unresolved cases: `{summary['unresolvedCases']}`",
            f"- status counts: `{json.dumps(summary['statusCounts'], sort_keys=True)}`",
            "",
            "## Cases",
            "",
            "| label | expected 2-primary order | visible Sha[2] order | state | status | missing factor |",
            "|---|---:|---:|---|---|---:|",
            *rows,
            "",
            "## Unresolved",
            "",
            *(unresolved or ["All higher 2-primary cases certified."]),
            "",
        ]
    )


def write_outputs(report: dict, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        HIGHER2_OUT: out_dir / HIGHER2_OUT,
        SUMMARY_OUT: out_dir / SUMMARY_OUT,
        UNRESOLVED_OUT: out_dir / UNRESOLVED_OUT,
    }
    outputs[HIGHER2_OUT].write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    outputs[SUMMARY_OUT].write_text(render_markdown(report))
    outputs[UNRESOLVED_OUT].write_text(json.dumps(unresolved_report(report), indent=2, sort_keys=True) + "\n")
    return outputs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run codex-2 higher 2-descent certificates without Magma.")
    parser.add_argument("--codex2-dir", help="Path to the codex-2 workspace.")
    parser.add_argument("--unresolved", help="Optional codex2_no_magma_unresolved.json path.")
    parser.add_argument("--out-dir", default=".", help="Directory for generated reports.")
    parser.add_argument("--timeout", type=int, default=240, help="Seconds allowed per mwrank case.")
    args = parser.parse_args(argv)

    codex2_dir = Path(args.codex2_dir).resolve() if args.codex2_dir else discover_codex2_dir()
    unresolved = Path(args.unresolved).resolve() if args.unresolved else None
    report = build_report(codex2_dir, unresolved, args.timeout)
    outputs = write_outputs(report, Path(args.out_dir))
    for name, path in outputs.items():
        print(f"wrote {name}: {path}")
    summary = report["summary"]
    print(f"cases={summary['totalCases']} certified={summary['certifiedCases']} unresolved={summary['unresolvedCases']}")


if __name__ == "__main__":
    main()
