"""Install the built wheel in an isolated environment and exercise its CLI.

Run after uv build: uv run --locked python tools/smoke_wheel.py
Only this development script invokes subprocesses; runtime validation never does.
"""

import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def smoke() -> None:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("*.whl"))
    if len(wheels) != 1:
        raise SystemExit("Expected exactly one wheel in dist; remove stale build artifacts first.")
    with TemporaryDirectory(prefix="env-contract-wheel-") as temporary:
        work = Path(temporary)
        environment = work / "venv"
        subprocess.run(
            ["uv", "venv", "--python", sys.executable, str(environment)],
            check=True,
            capture_output=True,
        )
        executables = environment / ("Scripts" if os.name == "nt" else "bin")
        python = executables / ("python.exe" if os.name == "nt" else "python")
        command = executables / (
            "env-contract-check.exe" if os.name == "nt" else "env-contract-check"
        )
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])],
            check=True,
            capture_output=True,
        )
        for example, expected in [("valid.env", 0), ("invalid.env", 1)]:
            result = subprocess.run(
                [
                    str(command),
                    "--contract",
                    str(root / "examples/env.contract.toml"),
                    "--env-file",
                    str(root / "examples" / example),
                    "--format",
                    "json",
                ],
                cwd=work,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != expected:
                raise SystemExit(f"Wheel smoke test failed for {example}.")
        result = subprocess.run(
            [str(python), "-m", "env_contract_check", "--version"],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or result.stdout.strip() != "0.1.0":
            raise SystemExit("Installed module entry point failed.")
    print("Wheel smoke checks passed; temporary environment removed.")


if __name__ == "__main__":
    smoke()
