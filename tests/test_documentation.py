"""Keep examples, local links, and the machine-readable protocol usable."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from env_contract_check import parse_contract, validate
from env_contract_check.cli import render
from env_contract_check.model import Issue, Report

ROOT = Path(__file__).parents[1]


def test_documented_json_schema_accepts_all_report_states() -> None:
    schema = json.loads((ROOT / "docs/output.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    contract = parse_contract('version=1\n[variables.X]\ntype="integer"')
    reports = [
        validate(contract, {"X": "1"}),
        validate(contract, {}),
        validate(contract, {"X": "bad", "EXTRA": "bad"}, strict=True, example={}),
        Report("error", 0, (Issue("dotenv.syntax", "Invalid assignment.", line=2),)),
    ]
    for report in reports:
        validator.validate(json.loads(render(report, json_output=True)))
    with pytest.raises(ValidationError):
        validator.validate(
            {
                "schema_version": 1,
                "status": "valid",
                "checked": 0,
                "issues": [],
                "leaked_value": "sensitive-canary",
            }
        )
    with pytest.raises(ValidationError):
        validator.validate({"schema_version": 1, "status": "invalid", "checked": 0, "issues": []})


def test_readme_python_example_runs(tmp_path: Path) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    examples = re.findall(r"```python\n(.*?)\n```", readme, flags=re.DOTALL)
    assert examples
    for example in examples:
        result = subprocess.run(
            [sys.executable, "-c", example],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr


def test_local_documentation_links_resolve() -> None:
    documents = [*ROOT.glob("*.md"), *ROOT.glob("docs/*.md"), ROOT / "llms.txt"]
    for document in documents:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            path = target.partition("#")[0]
            assert (document.parent / path).exists(), f"{document.name}: broken link {target}"
