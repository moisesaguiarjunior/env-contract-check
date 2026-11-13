"""Run the real composite shell step as a local pre-deployment gate."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]
pytestmark = pytest.mark.skipif(
    os.name == "nt" or shutil.which("bash") is None or shutil.which("uv") is None,
    reason="The composite shell adapter is currently verified with Bash and uv on Unix runners.",
)


@pytest.fixture
def consumer(tmp_path: Path) -> Path:
    (tmp_path / "contract.toml").write_text(
        'version=1\n[variables.PORT]\ntype="integer"\nmin=1\nmax=65535', encoding="utf-8"
    )
    (tmp_path / "generated.env").write_text("PORT=8080", encoding="utf-8")
    return tmp_path


def run_gate(consumer: Path, **inputs: str) -> subprocess.CompletedProcess[str]:
    metadata = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    script = metadata["runs"]["steps"][1]["run"]
    assert isinstance(script, str)
    env = dict(os.environ)
    env.update(
        CHECK_ACTION_ROOT=str(ROOT),
        CHECK_CONTRACT="contract.toml",
        CHECK_ENV_FILE="generated.env",
        CHECK_EXAMPLE="",
        CHECK_STRICT="false",
        CHECK_FORMAT="json",
        CHECK_PYTHON=f"{sys.version_info.major}.{sys.version_info.minor}",
        UV_OFFLINE="true",
    )
    env.update(inputs)
    return subprocess.run(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-e",
            "-o",
            "pipefail",
            "-c",
            script + "\nprintf deployed > deployment.marker\n",
        ],
        cwd=consumer,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_file_allows_next_deployment_step(consumer: Path) -> None:
    result = run_gate(consumer)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "valid"
    assert (consumer / "deployment.marker").read_text() == "deployed"


@pytest.mark.parametrize("content", ["PORT=sensitive-canary", "", "PORT=1\nPORT=2"])
def test_invalid_generated_environment_blocks_deployment(consumer: Path, content: str) -> None:
    (consumer / "generated.env").write_text(content, encoding="utf-8")
    result = run_gate(consumer)
    assert result.returncode in {1, 2}, result.stderr
    assert not (consumer / "deployment.marker").exists()
    assert "sensitive-canary" not in result.stdout + result.stderr


def test_missing_generated_file_blocks_deployment(consumer: Path) -> None:
    result = run_gate(consumer, CHECK_ENV_FILE="not-present.env")
    assert result.returncode == 2
    assert json.loads(result.stdout)["issues"][0]["code"] == "input.unreadable"
    assert not (consumer / "deployment.marker").exists()


def test_example_drift_blocks_deployment(consumer: Path) -> None:
    (consumer / "example.env").write_text("OLD=", encoding="utf-8")
    result = run_gate(consumer, CHECK_EXAMPLE="example.env")
    assert result.returncode == 1
    assert "example.missing" in result.stdout
    assert not (consumer / "deployment.marker").exists()


def test_strict_mode_blocks_undeclared_values(consumer: Path) -> None:
    (consumer / "generated.env").write_text("PORT=8080\nOLD=secret", encoding="utf-8")
    result = run_gate(consumer, CHECK_STRICT="true")
    assert result.returncode == 1
    assert "value.unexpected" in result.stdout
    assert "secret" not in result.stdout
    assert not (consumer / "deployment.marker").exists()


@pytest.mark.parametrize(
    "name", ["file with spaces.env", "$(touch EXECUTED).env", "; touch EXECUTED.env"]
)
def test_paths_are_data_not_shell_expressions(consumer: Path, name: str) -> None:
    (consumer / name).write_text("PORT=8080", encoding="utf-8")
    result = run_gate(consumer, CHECK_ENV_FILE=name)
    assert result.returncode == 0, result.stderr
    assert not (consumer / "EXECUTED").exists()
    assert not (consumer / "EXECUTED.env").exists()


def test_invalid_boolean_input_fails_without_echoing_it(consumer: Path) -> None:
    result = run_gate(consumer, CHECK_STRICT="sensitive-canary")
    assert result.returncode == 2
    assert "sensitive-canary" not in result.stdout + result.stderr
    assert not (consumer / "deployment.marker").exists()


def test_invalid_format_input_blocks_deployment(consumer: Path) -> None:
    result = run_gate(consumer, CHECK_FORMAT="sensitive-canary")
    assert result.returncode == 2
    assert "sensitive-canary" not in result.stdout + result.stderr
    assert not (consumer / "deployment.marker").exists()
