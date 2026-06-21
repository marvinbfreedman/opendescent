"""Magma-free completion exporter for the codex-2 BSD worklist."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .sage_primary import run_sage_primary_probe


PRIMARY_OUT = "codex2_no_magma_primary_evidence.json"
SUMMARY_OUT = "codex2_no_magma_completion_summary.md"
UNRESOLVED_OUT = "codex2_no_magma_unresolved.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _candidate_codex2_dirs() -> list[Path]:
    cwd = Path.cwd()
    candidates = []
    env_dir = os.environ.get("CODEX2_DIR")
    if env_dir:
        candidates.append(Path(env_dir))
    candidates.extend(
        [
            cwd / "codex-2",
            cwd.parent / "codex-2",
            cwd.parent.parent / "codex-2",
            Path("/Users/mbf_mini/p3/codex-2"),
        ]
    )
    return candidates


def discover_codex2_dir() -> Path:
    for path in _candidate_codex2_dirs():
        if (path / "bsd_primary_descent_tasks.json").exists():
            return path
    raise FileNotFoundError(
        "could not find codex-2; pass --codex2-dir or set CODEX2_DIR"
    )


def _standard_case(row: dict, source: str) -> dict:
    coeffs = row.get("weierstrass") or row.get("aInvariants") or row.get("a_invariants")
    expected_primary = (
        row.get("targetPrimaryOrder")
        or row.get("predictedShaPrimaryOrder")
        or row.get("predictedShaOrder")
    )
    return {
        "label": row["label"],
        "conductor": row.get("conductor"),
        "weierstrass": [int(value) for value in coeffs],
        "prime": int(row["prime"]),
        "expectedPrimaryOrder": int(expected_primary) if expected_primary is not None else None,
        "expectedSelmerOrder": row.get("expectedSelmerOrder"),
        "predictedShaOrder": row.get("predictedShaOrder"),
        "predictedShaFactorization": row.get("predictedShaFactorization"),
        "sourceArtifact": source,
    }


def _merge_case(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    for key, value in incoming.items():
        if merged.get(key) is None and value is not None:
            merged[key] = value
    sources = set(str(merged.get("sourceArtifact", "")).split(", "))
    sources.update(str(incoming.get("sourceArtifact", "")).split(", "))
    merged["sourceArtifact"] = ", ".join(sorted(source for source in sources if source))
    return merged


def load_codex2_worklist(codex2_dir: Path) -> list[dict]:
    cases: dict[tuple[str, int], dict] = {}
    primary_path = codex2_dir / "bsd_primary_descent_tasks.json"
    primary = _load_json(primary_path)

    groups = [
        ("selectedThreeSelmerTasks", "bsd_primary_descent_tasks:selectedThreeSelmerTasks"),
        ("threeSelmerTasks", "bsd_primary_descent_tasks:threeSelmerTasks"),
        ("twoDescentAuditTasks", "bsd_primary_descent_tasks:twoDescentAuditTasks"),
        ("externalDescentTasks", "bsd_primary_descent_tasks:externalDescentTasks"),
    ]
    for key, source in groups:
        for row in primary.get(key, []):
            case = _standard_case(row, source)
            ident = (case["label"], case["prime"])
            cases[ident] = _merge_case(cases[ident], case) if ident in cases else case

    p5_path = codex2_dir / "bsd_5primary_probe.json"
    if p5_path.exists():
        for row in _load_json(p5_path).get("tasks", []):
            case = _standard_case({**row, "prime": 5}, "bsd_5primary_probe:tasks")
            ident = (case["label"], case["prime"])
            cases[ident] = _merge_case(cases[ident], case) if ident in cases else case

    p2_path = codex2_dir / "bsd_2primary_audit.json"
    if p2_path.exists():
        for row in _load_json(p2_path).get("rows", []):
            case = _standard_case(
                {
                    "label": row["label"],
                    "conductor": row.get("conductor"),
                    "aInvariants": row.get("aInvariants"),
                    "prime": 2,
                    "targetPrimaryOrder": row.get("bsd", {}).get("predictedSha2PrimaryOrder"),
                    "expectedSelmerOrder": row.get("twoSelmer", {}).get("order"),
                    "predictedShaOrder": row.get("bsd", {}).get("predictedShaOrder"),
                    "predictedShaFactorization": "2^4",
                },
                "bsd_2primary_audit:rows",
            )
            ident = (case["label"], case["prime"])
            cases[ident] = _merge_case(cases[ident], case) if ident in cases else case

    return sorted(cases.values(), key=lambda case: (case["prime"], case["conductor"] or 0, case["label"]))


def completion_summary(cases: list[dict]) -> dict:
    statuses = Counter(case["evidence"]["status"] for case in cases)
    by_prime: dict[str, dict[str, int]] = defaultdict(dict)
    for case in cases:
        by_prime[str(case["prime"])][case["evidence"]["status"]] = (
            by_prime[str(case["prime"])].get(case["evidence"]["status"], 0) + 1
        )
    certified = [
        case["label"]
        for case in cases
        if case["evidence"].get("certificationState") == "certified"
    ]
    unresolved = [
        case["label"]
        for case in cases
        if case["evidence"].get("certificationState") != "certified"
    ]
    return {
        "totalCases": len(cases),
        "certifiedCases": len(certified),
        "unresolvedCases": len(unresolved),
        "certifiedLabels": certified,
        "unresolvedLabels": unresolved,
        "statusCounts": dict(sorted(statuses.items())),
        "statusCountsByPrime": {prime: dict(sorted(rows.items())) for prime, rows in sorted(by_prime.items())},
    }


def evaluate_worklist(codex2_dir: Path, timeout: int) -> dict:
    cases = []
    for case in load_codex2_worklist(codex2_dir):
        print(f"running {case['label']} p={case['prime']}...", flush=True)
        probe = run_sage_primary_probe(case, timeout=timeout)
        evidence = probe["evidence"]
        print(
            f"finished {case['label']} p={case['prime']}: "
            f"{evidence.get('certificationState')} / {evidence.get('status')}",
            flush=True,
        )
        cases.append(
            {
                **case,
                "evidence": evidence,
                "backendReturncode": probe["returncode"],
                "backendTimedOut": probe["timedOut"],
                "backendStderr": probe["stderr"],
                "rawBackendResult": probe["raw"],
            }
        )
    return {
        "artifact": "codex2_no_magma_primary_evidence",
        "policy": "no_magma",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "codex2Dir": str(codex2_dir),
        "backend": "sage",
        "timeoutSecondsPerCase": timeout,
        "summary": completion_summary(cases),
        "cases": cases,
    }


def unresolved_report(report: dict) -> dict:
    unresolved = [
        case
        for case in report["cases"]
        if case["evidence"].get("certificationState") != "certified"
    ]
    return {
        "artifact": "codex2_no_magma_unresolved",
        "policy": "no_magma",
        "sourceArtifact": PRIMARY_OUT,
        "summary": completion_summary(unresolved),
        "cases": unresolved,
    }


def _status_label(case: dict) -> str:
    evidence = case["evidence"]
    return str(evidence.get("status") or evidence.get("certificationState"))


def render_markdown(report: dict) -> str:
    rows = []
    for case in report["cases"]:
        evidence = case["evidence"]
        primary = evidence.get("pPrimaryOrder") or evidence.get("pPrimaryBoundOrder") or evidence.get("twoSelmerBound")
        rows.append(
            "| `{label}` | {prime} | {expected} | `{state}` | `{status}` | {primary} |".format(
                label=case["label"],
                prime=case["prime"],
                expected=case.get("expectedPrimaryOrder"),
                state=evidence.get("certificationState"),
                status=_status_label(case),
                primary=primary if primary is not None else "",
            )
        )
    unresolved = [
        f"- `{case['label']}` p={case['prime']}: {case['evidence'].get('reason')}"
        for case in report["cases"]
        if case["evidence"].get("certificationState") != "certified"
    ]
    summary = report["summary"]
    return "\n".join(
        [
            "# codex-2 Magma-Free Completion Summary",
            "",
            "This report uses Sage/eclib evidence only.  Exact primary-order",
            "certification is recorded only when Sage proves the primary order.",
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
            "| label | p | expected primary order | state | status | Sage value |",
            "|---|---:|---:|---|---|---:|",
            *rows,
            "",
            "## Unresolved",
            "",
            *(unresolved or ["All cases certified by the no-Magma path."]),
            "",
            "## Re-run",
            "",
            "```bash",
            "python3 codex2_no_magma_completion.py --codex2-dir /Users/mbf_mini/p3/codex-2",
            "```",
            "",
        ]
    )


def write_outputs(report: dict, out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    unresolved = unresolved_report(report)
    outputs = {
        PRIMARY_OUT: out_dir / PRIMARY_OUT,
        SUMMARY_OUT: out_dir / SUMMARY_OUT,
        UNRESOLVED_OUT: out_dir / UNRESOLVED_OUT,
    }
    outputs[PRIMARY_OUT].write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    outputs[SUMMARY_OUT].write_text(render_markdown(report))
    outputs[UNRESOLVED_OUT].write_text(json.dumps(unresolved, indent=2, sort_keys=True) + "\n")
    return outputs


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the codex-2 BSD worklist without Magma.")
    parser.add_argument("--codex2-dir", help="Path to the codex-2 workspace.")
    parser.add_argument("--out-dir", default=".", help="Directory for generated reports.")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds allowed per Sage case.")
    args = parser.parse_args(argv)

    codex2_dir = Path(args.codex2_dir).resolve() if args.codex2_dir else discover_codex2_dir()
    report = evaluate_worklist(codex2_dir, timeout=args.timeout)
    outputs = write_outputs(report, Path(args.out_dir))
    for name, path in outputs.items():
        print(f"wrote {name}: {path}")
    summary = report["summary"]
    print(f"cases={summary['totalCases']} certified={summary['certifiedCases']} unresolved={summary['unresolvedCases']}")


if __name__ == "__main__":
    main()
