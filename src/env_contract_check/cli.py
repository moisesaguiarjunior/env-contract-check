"""CLI adapter: explicit sources, bounded reads, safe errors, stable output."""

import argparse
import json
import os
import sys
from collections.abc import Sequence
from dataclasses import asdict, replace
from importlib.metadata import version
from pathlib import Path
from typing import NoReturn

from env_contract_check.contract import parse_contract
from env_contract_check.dotenv import parse_dotenv
from env_contract_check.model import InputError, Issue, Report
from env_contract_check.validation import validate

_MAX_BYTES = 1024 * 1024


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        # argparse errors can echo arbitrary tokens, including accidentally pasted secrets.
        raise InputError(
            Issue("cli.arguments", "Invalid arguments. Run env-contract-check --help.")
        )


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(description="Validate environment variables without printing their values.")
    parser.add_argument("--version", action="version", version=version("env-contract-check"))
    parser.add_argument(
        "--contract", type=Path, required=True, help="Path to a version 1 TOML contract"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--env-file", type=Path, help="Validate only this literal .env file")
    source.add_argument(
        "--process-env", action="store_true", help="Validate only the process environment"
    )
    parser.add_argument(
        "--example-file", type=Path, help="Check that example keys exactly match the contract"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Reject undeclared environment variables"
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default="text", help="Output format (default: text)"
    )
    parser.allow_abbrev = False
    return parser


def _read(path: Path, label: str) -> str:
    try:
        with path.open("rb") as stream:
            data = stream.read(_MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise InputError(Issue("input.too_large", f"The {label} exceeds the 1 MiB limit."))
        return data.decode("utf-8-sig")
    except (OSError, UnicodeError):
        raise InputError(Issue("input.unreadable", f"Cannot read the {label} as UTF-8.")) from None


def _dotenv_file(path: Path, label: str) -> dict[str, str]:
    text = _read(path, label)
    try:
        return parse_dotenv(text)
    except InputError as error:
        contextual_issue = replace(error.issue, message=f"In {label}: {error.issue.message}")
        raise InputError(contextual_issue) from None


def render(report: Report, *, json_output: bool) -> str:
    """Serialize safe report data; JSON schema version is independent of package version."""
    if json_output:
        return json.dumps({"schema_version": 1, **asdict(report)}, sort_keys=True)
    if report.status == "valid":
        return f"PASS: {report.checked} declared variables checked."
    lines = [f"{report.status.upper()}: {len(report.issues)} issue(s)."]
    for issue in report.issues:
        location = f" {issue.variable}" if issue.variable else ""
        if issue.line is not None:
            location += f" line {issue.line}"
        lines.append(f"  [{issue.code}]{location}: {issue.message}")
    return "\n".join(lines)


def _wants_json(args: Sequence[str]) -> bool:
    # Respect machine output even when argument parsing fails. Last format wins.
    choice = "text"
    for index, arg in enumerate(args):
        if arg.startswith("--format="):
            choice = arg.partition("=")[2]
        elif arg == "--format" and index + 1 < len(args):
            choice = args[index + 1]
    return choice == "json"


def main(argv: Sequence[str] | None = None) -> int:
    """Return 0 for valid, 1 for violations, 2 for input/usage errors.

    Reports use stdout in both formats. Help and version follow argparse conventions.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        options = _parser().parse_args(args)
        contract = parse_contract(_read(options.contract, "contract"))
        values = (
            dict(os.environ)
            if options.process_env
            else _dotenv_file(options.env_file, "environment file")
        )
        example = (
            _dotenv_file(options.example_file, "example file")
            if options.example_file is not None
            else None
        )
        report = validate(contract, values, strict=options.strict, example=example)
    except InputError as error:
        report = Report("error", 0, (error.issue,))
    try:
        print(render(report, json_output=_wants_json(args)))
    except BrokenPipeError:
        return 2
    return report.exit_code
