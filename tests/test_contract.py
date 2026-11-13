"""Contract failures must be explicit, closed, and safe to report."""

import pytest

from env_contract_check import InputError, parse_contract
from env_contract_check.model import Kind


def test_loads_sorted_immutable_rules() -> None:
    contract = parse_contract("""
version = 1
[variables.Z]
type = "string"
required = false
allow_empty = true
choices = ["", "demo"]
[variables.A]
type = "integer"
min = -10
max = 10
""")
    assert [rule.name for rule in contract.rules] == ["A", "Z"]
    assert contract.rules[0].kind == Kind.INTEGER
    assert contract.rules[1].choices == ("", "demo")
    assert not contract.rules[1].required


@pytest.mark.parametrize(
    "text",
    [
        "",
        "version = true",
        "version = 2",
        'version = "1"',
        "version = 1\nvariables = []",
        "version = 1\n[variables]",
        'version = 1\nunknown = "sensitive-canary"',
        'version = 1\n[variables."BAD-NAME"]\ntype = "string"',
        'version = 1\n[variables."\\u001bSECRET"]\ntype = "string"',
        'version = 1\n[variables.X]\ntype = "unclosed',
        "version = 1\nversion = 1",
        'version = 1\n[variables.X]\ntype = "string"\ntype = "string"',
    ],
)
def test_rejects_invalid_contracts_without_echoing_input(text: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_contract(text)
    assert caught.value.issue.code == "contract.invalid"
    assert "sensitive-canary" not in str(caught.value)
    assert "\x1b" not in str(caught.value)


@pytest.mark.parametrize(
    "definition",
    [
        'X = "string"',
        '[X]\ntype = "unknown"',
        "[X]\ntype = 3",
        "[X]\nrequired = true",
        '[X]\ntype = "string"\nrequried = true',
        '[X]\ntype = "string"\nrequired = 1',
        '[X]\ntype = "string"\nallow_empty = "false"',
        '[X]\ntype = "integer"\nmin = true',
        '[X]\ntype = "integer"\nmax = 1.5',
        '[X]\ntype = "integer"\nmin = 3\nmax = 2',
        '[X]\ntype = "string"\nmin = 2',
        '[X]\ntype = "integer"\nallow_empty = false',
        '[X]\ntype = "integer"\nchoices = ["1"]',
        '[X]\ntype = "string"\nchoices = []',
        '[X]\ntype = "string"\nchoices = "a"',
        '[X]\ntype = "string"\nchoices = [1]',
        '[X]\ntype = "string"\nchoices = ["a", "a"]',
        '[X]\ntype = "string"\nchoices = [""]',
    ],
)
def test_rejects_invalid_rule_combinations(definition: str) -> None:
    # Prefix rule tables while preserving the scalar-variable negative case.
    text = "version = 1\n[variables]\n" + definition.replace("[X]", "[variables.X]")
    with pytest.raises(InputError):
        parse_contract(text)
