"""Exercise CLI source isolation, exit codes, and packaging entry points."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from env_contract_check.cli import main

CONTRACT = 'version = 1\n[variables.PORT]\ntype = "integer"\nmin = 1\nmax = 65535\n'


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[Path, Path]:
    contract = tmp_path / "contract.toml"
    env = tmp_path / "input.env"
    contract.write_text(CONTRACT, encoding="utf-8")
    env.write_text("PORT=8080", encoding="utf-8")
    return contract, env


def arguments(inputs: tuple[Path, Path]) -> list[str]:
    contract, env = inputs
    return ["--contract", str(contract), "--env-file", str(env)]


def test_valid_cli_and_exact_example_match(
    inputs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    example = tmp_path / "example.env"
    example.write_text("PORT=placeholder", encoding="utf-8")
    assert main([*arguments(inputs), "--example-file", str(example), "--strict"]) == 0
    assert capsys.readouterr().out == "PASS: 1 declared variables checked.\n"


def test_invalid_json_has_stable_fields_and_no_values(
    inputs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs[1].write_text("PORT=sensitive-canary", encoding="utf-8")
    assert main([*arguments(inputs), "--format=json"]) == 1
    output = capsys.readouterr()
    assert not output.err
    assert "sensitive-canary" not in output.out
    assert json.loads(output.out) == {
        "schema_version": 1,
        "status": "invalid",
        "checked": 1,
        "issues": [
            {
                "code": "value.integer",
                "variable": "PORT",
                "line": None,
                "message": "Expected a decimal integer.",
            }
        ],
    }


def test_file_source_does_not_fall_back_to_process(
    inputs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PORT", "8080")
    inputs[1].write_text("", encoding="utf-8")
    assert main(arguments(inputs)) == 1
    assert "value.missing" in capsys.readouterr().out
    assert os.environ["PORT"] == "8080"


def test_process_source_is_explicit(
    inputs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PORT", "8080")
    inputs[1].write_text("PORT=bad", encoding="utf-8")
    assert main(["--contract", str(inputs[0]), "--process-env"]) == 0
    assert "PASS" in capsys.readouterr().out


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--unknown", "sensitive-canary"],
        ["--format", "sensitive-canary"],
        ["--contract", "sensitive-canary"],
        ["--contract"],
        ["--contract", "missing", "--process-env", "--env-file", "other"],
        ["--contr", "missing", "--process-env"],
    ],
)
def test_usage_errors_are_safe_and_machine_readable(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([*args, "--format", "json"]) == 2
    output = capsys.readouterr()
    document = json.loads(output.out)
    assert document["status"] == "error"
    assert document["issues"][0]["code"] == "cli.arguments"
    assert "sensitive-canary" not in output.out + output.err


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"PORT=one\nPORT=two", "dotenv.duplicate"),
        (b"PORT=\xff", "input.unreadable"),
        (b"X=" + b"a" * 1024 * 1024, "input.too_large"),
        (b"sensitive-canary", "dotenv.syntax"),
    ],
)
def test_input_errors_are_safe(
    inputs: tuple[Path, Path],
    content: bytes,
    code: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs[1].write_bytes(content)
    assert main([*arguments(inputs), "--format", "json"]) == 2
    output = capsys.readouterr().out
    assert json.loads(output)["issues"][0]["code"] == code
    assert "sensitive-canary" not in output
    assert str(inputs[1]) not in output


def test_missing_file_does_not_expose_path(
    inputs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs[1].unlink()
    assert main(arguments(inputs)) == 2
    output = capsys.readouterr().out
    assert "input.unreadable" in output
    assert str(inputs[1]) not in output


def test_contract_parser_error_does_not_expose_document(
    inputs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    inputs[0].write_text('version = "sensitive-canary', encoding="utf-8")
    assert main(arguments(inputs)) == 2
    assert "sensitive-canary" not in capsys.readouterr().out


def test_module_entrypoint_works_without_repository_cwd(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "env_contract_check", "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "0.1.0"
    assert result.stderr == ""


def test_console_entrypoint_checks_packaged_examples() -> None:
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [
            "env-contract-check",
            "--contract",
            str(root / "examples/env.contract.toml"),
            "--env-file",
            str(root / "examples/valid.env"),
            "--example-file",
            str(root / "examples/.env.example"),
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "4 declared variables" in result.stdout


def test_help_is_available(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        main(["--help"])
    assert caught.value.code == 0
    assert "--process-env" in capsys.readouterr().out


def test_example_syntax_error_identifies_source_without_exposing_path(
    inputs: tuple[Path, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    example = tmp_path / "sensitive-canary.env"
    example.write_text("PORT=1\nPORT=2", encoding="utf-8")
    assert main([*arguments(inputs), "--example-file", str(example)]) == 2
    output = capsys.readouterr().out
    assert "In example file:" in output
    assert "line 2" in output
    assert "sensitive-canary" not in output


@pytest.mark.parametrize("output_format", ["text", "json"])
def test_closed_real_output_pipe_exits_cleanly(
    inputs: tuple[Path, Path], output_format: str
) -> None:
    reader, writer = os.pipe()
    os.close(reader)
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "env_contract_check",
                *arguments(inputs),
                "--format",
                output_format,
            ],
            stdout=writer,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    finally:
        os.close(writer)
    assert result.returncode == 2
    assert result.stderr == ""


@pytest.mark.parametrize("allow_empty", [True, False])
def test_leading_hash_is_validated_as_a_value(
    inputs: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
    allow_empty: bool,
) -> None:
    inputs[0].write_text(
        'version=1\n[variables.TOKEN]\ntype="string"\n'
        f'allow_empty={str(allow_empty).lower()}\nchoices=["#synthetic"]',
        encoding="utf-8",
    )
    inputs[1].write_text("TOKEN=#synthetic", encoding="utf-8")
    assert main(arguments(inputs)) == 0
    assert "#synthetic" not in capsys.readouterr().out
    inputs[0].write_text(
        'version=1\n[variables.TOKEN]\ntype="string"\nallow_empty=true\nchoices=[""]',
        encoding="utf-8",
    )
    assert main(arguments(inputs)) == 1
    assert "value.choice" in capsys.readouterr().out
