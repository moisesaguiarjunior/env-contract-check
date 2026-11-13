"""Behavioral and generative checks for the pure validation boundary."""

import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from env_contract_check import parse_contract, validate
from env_contract_check.cli import render


def contract(kind: str, extra: str = "") -> str:
    return f'version = 1\n[variables.VALUE]\ntype = "{kind}"\n{extra}'


@pytest.mark.parametrize(
    ("kind", "value", "valid"),
    [
        ("integer", "42", True),
        ("integer", "+01", True),
        ("integer", "-3", True),
        ("integer", "1_000", False),
        ("integer", "1.0", False),
        ("integer", "\u0661", False),
        ("integer", " 1", False),
        ("integer", "9" * 641, False),
        ("boolean", "TRUE", True),
        ("boolean", "false", True),
        ("boolean", "1", True),
        ("boolean", "0", True),
        ("boolean", "yes", False),
        ("boolean", "False ", False),
        ("url", "https://example.com/path?x=1#fragment", True),
        ("url", "postgresql://demo:fake@localhost:5432/db", True),
        ("url", "redis://[::1]:6379", True),
        ("url", "https://example.com/%20", True),
        ("url", "https://example.com/%zz", False),
        ("url", "relative", False),
        ("url", "mailto:hello@example.com", False),
        ("url", "file:///tmp/file", False),
        ("url", "https://", False),
        ("url", "https://host:99999", False),
        ("url", "https://host:abc", False),
        ("url", "https://host:", False),
        ("url", "https://host:0", False),
        ("url", "https://[bad", False),
        ("url", "\nhttps://host", False),
        ("url", "https://example.com/a b", False),
        ("url", "https://a\\b", False),
        ("string", "anything", True),
        ("string", " ", True),
        ("string", "", False),
    ],
)
def test_type_contract(kind: str, value: str, valid: bool) -> None:
    report = validate(parse_contract(contract(kind)), {"VALUE": value})
    assert (report.status == "valid") is valid
    assert report.exit_code == (0 if valid else 1)


def test_missing_optional_empty_and_choices_have_distinct_semantics() -> None:
    parsed = parse_contract(contract("string", 'required = false\nchoices = ["dev"]'))
    assert validate(parsed, {}).status == "valid"
    assert validate(parsed, {"VALUE": ""}).issues[0].code == "value.empty"
    assert validate(parsed, {"VALUE": "prod"}).issues[0].code == "value.choice"
    assert validate(parsed, {"VALUE": "dev"}).status == "valid"
    empty = parse_contract(contract("string", 'allow_empty = true\nchoices = [""]'))
    assert validate(empty, {"VALUE": ""}).status == "valid"
    assert validate(empty, {}).issues[0].code == "value.missing"


@given(st.integers(min_value=-1000, max_value=1000))
def test_integer_boundaries(number: int) -> None:
    parsed = parse_contract(contract("integer", "min = -10\nmax = 10"))
    assert (validate(parsed, {"VALUE": str(number)}).status == "valid") == (-10 <= number <= 10)


def test_example_keys_include_optional_variables_and_ignore_placeholder_values() -> None:
    parsed = parse_contract(contract("integer", "required = false"))
    assert validate(parsed, {}, example={"VALUE": "placeholder"}).status == "valid"
    report = validate(parsed, {}, example={"OLD": ""})
    assert [issue.code for issue in report.issues] == ["example.missing", "example.unexpected"]


def test_strict_is_opt_in_and_unsafe_external_names_are_not_printed() -> None:
    parsed = parse_contract(contract("string"))
    values = {"VALUE": "demo", "UNUSED": "secret", "BAD\x1bNAME": "secret"}
    assert validate(parsed, values).status == "valid"
    report = validate(parsed, values, strict=True)
    assert [issue.variable for issue in report.issues] == [None, "UNUSED"]
    assert "BAD" not in render(report, json_output=True)


@given(st.text(min_size=1, max_size=200))
def test_reports_do_not_serialize_supplied_values(value: str) -> None:
    # The prefix makes collision with fixed diagnostic text impossible.
    secret = "sensitive-canary:" + value
    report = validate(parse_contract(contract("integer")), {"VALUE": secret})
    document = json.loads(render(report, json_output=True))
    assert document["status"] == "invalid"
    assert secret not in str(document)
    assert secret not in render(report, json_output=False)


@pytest.mark.parametrize("kind", ["string", "integer", "boolean", "url"])
@given(st.text(max_size=300))
def test_every_type_handles_arbitrary_strings_without_crashing(kind: str, value: str) -> None:
    report = validate(parse_contract(contract(kind)), {"VALUE": value})
    assert report.status in {"valid", "invalid"}
