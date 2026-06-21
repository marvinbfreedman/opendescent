"""Backend registry for OpenDescent certificate engines."""

from __future__ import annotations

import json
import os
import shutil
import subprocess


BACKENDS = ("native", "sage", "mwrank_direct", "pari_gp", "magma")


def available_backends() -> dict[str, dict]:
    return {
        "native": {
            "available": True,
            "kind": "built-in",
            "description": "OpenDescent native arithmetic scaffold",
        },
        "sage": {
            "available": shutil.which("sage") is not None,
            "kind": "open-source external",
            "description": "Sage/eclib rank bounds, Selmer rank, and torsion",
        },
        "pari_gp": {
            "available": shutil.which("gp") is not None,
            "kind": "planned external",
            "description": "PARI/GP adapter placeholder",
        },
        "mwrank_direct": {
            "available": shutil.which("mwrank") is not None,
            "kind": "open-source external",
            "description": "Direct eclib/mwrank rank and 2-Selmer adapter",
        },
        "magma": {
            "available": shutil.which("magma") is not None,
            "kind": "optional licensed external",
            "description": "Detector only; Magma is not bundled or required",
        },
    }


def unavailable_backend_result(name: str) -> dict:
    info = available_backends().get(name, {})
    return {
        "backend": name,
        "succeeded": False,
        "parsed": None,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "error": f"backend '{name}' is not implemented in OpenDescent yet",
        "available": info.get("available", False),
    }


def run_sage_backend(input_path: str) -> dict:
    env = dict(os.environ)
    cwd = os.getcwd()
    env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        ["sage", "-python", "-m", "opendescent.sage_backend", input_path],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    result = {
        "command": "sage -python -m opendescent.sage_backend",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "succeeded": proc.returncode == 0,
        "parsed": None,
    }
    try:
        result["parsed"] = json.loads(proc.stdout)
    except Exception:
        pass
    return result


def run_mwrank_backend(input_path: str) -> dict:
    env = dict(os.environ)
    cwd = os.getcwd()
    env["PYTHONPATH"] = cwd + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        ["python3", "-m", "opendescent.mwrank_backend", input_path],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    result = {
        "command": "python3 -m opendescent.mwrank_backend",
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "succeeded": proc.returncode == 0,
        "parsed": None,
    }
    try:
        result["parsed"] = json.loads(proc.stdout)
    except Exception:
        pass
    return result


def run_backend(name: str, input_path: str | None) -> dict | None:
    if name == "native":
        return None
    if name == "sage":
        if input_path is None:
            raise ValueError("input_path is required for the Sage backend")
        return run_sage_backend(input_path)
    if name == "mwrank_direct":
        if input_path is None:
            raise ValueError("input_path is required for the mwrank backend")
        return run_mwrank_backend(input_path)
    return unavailable_backend_result(name)
