"""Direct eclib/mwrank backend.

This adapter is intentionally small: it runs the installed ``mwrank`` binary for
each input curve and translates the public text output into OpenDescent's JSON
certificate protocol.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys


RANK_RE = re.compile(r"^Rank\s*=\s*(\d+)", re.MULTILINE)
SELMER_RE = re.compile(r"^Rank of S\^2\(E\)\s*=\s*(\d+)", re.MULTILINE)
GENERATOR_RE = re.compile(r"^Generator\s+(\d+)\s+is\s+([^;]+);\s+height\s+([0-9.eE+-]+)", re.MULTILINE)
REGULATOR_RE = re.compile(r"^Regulator\s*=\s*([0-9.eE+-]+)", re.MULTILINE)


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_mwrank_output(label: str, returncode: int, output: str) -> dict:
    rank = _int_or_none((RANK_RE.search(output) or [None, None])[1])
    selmer = _int_or_none((SELMER_RE.search(output) or [None, None])[1])
    unconditional = "determined unconditionally" in output
    certified = returncode == 0 and unconditional and rank is not None
    regulator_match = REGULATOR_RE.search(output)
    generators = [
        {
            "index": int(match.group(1)),
            "point": match.group(2).strip(),
            "height": _float_or_none(match.group(3)),
        }
        for match in GENERATOR_RE.finditer(output)
    ]

    return {
        "label": label,
        "engine": "mwrank_direct",
        "rankLowerBound": rank,
        "rankUpperBound": rank if certified else None,
        "rankInterval": [rank, rank] if certified else None,
        "rankCertified": certified,
        "twoSelmerRank": selmer,
        "selmerUpperBound": selmer,
        "torsionOrder": None,
        "rankSource": "mwrank:Rank",
        "selmerSource": "mwrank:Rank of S^2(E)" if selmer is not None else None,
        "selmerError": None if selmer is not None else "mwrank Selmer rank line not found",
        "regulator": _float_or_none(regulator_match.group(1)) if regulator_match else None,
        "generators": generators,
        "returncode": returncode,
        "success": returncode == 0,
        "status": "certified rank interval" if certified else "mwrank output did not close the rank interval",
        "rawOutput": output,
    }


def run_one_curve(row: dict) -> dict:
    coeffs = row["weierstrass"]
    label = row.get("label", "curve")
    curve_text = "[" + ",".join(str(int(c)) for c in coeffs) + "]"
    proc = subprocess.run(
        ["mwrank"],
        input=curve_text + "\n",
        capture_output=True,
        text=True,
        check=False,
    )
    return parse_mwrank_output(label, proc.returncode, proc.stdout + proc.stderr)


def main() -> None:
    if len(sys.argv) != 2:
        print(json.dumps({"success": False, "error": "usage: python3 -m opendescent.mwrank_backend input.json"}))
        raise SystemExit(2)
    if shutil.which("mwrank") is None:
        print(
            json.dumps(
                {
                    "artifact": "opendescent_mwrank_backend",
                    "success": False,
                    "curves": {},
                    "failures": {
                        "environment": {
                            "success": False,
                            "error": "mwrank executable not found in PATH",
                        }
                    },
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise SystemExit(1)

    payload = json.load(open(sys.argv[1]))
    curves = {}
    failures = {}
    for row in payload.get("curves", []):
        label = row.get("label", "curve")
        try:
            curves[label] = run_one_curve(row)
        except Exception as exc:
            failures[label] = {"success": False, "error": str(exc)}

    all_success = bool(curves) and all(row.get("success") for row in curves.values()) and not failures
    print(
        json.dumps(
            {
                "artifact": "opendescent_mwrank_backend",
                "success": all_success,
                "curves": curves,
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    raise SystemExit(0 if all_success else 1)


if __name__ == "__main__":
    main()
