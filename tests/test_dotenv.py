"""Examples define the intentionally narrow dotenv grammar."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from env_contract_check import InputError, parse_dotenv


def test_literal_syntax_comments_bom_and_crlf() -> None:
    assert parse_dotenv("""\ufeff# Comment\r
export A = value # comment\r
B="two words # literal" # comment
C='literal $HOME \\n'
D=https://example.com/#fragment
EMPTY=
HASH= # comment
""") == {
        "A": "value",
        "B": "two words # literal",
        "C": "literal $HOME \\n",
        "D": "https://example.com/#fragment",
        "EMPTY": "",
        "HASH": "",
    }


@pytest.mark.parametrize(
    "text",
    [
        "X",
        "=value",
        "BAD-NAME=value",
        "3X=value",
        'X="unterminated',
        'X="closed"junk',
        'X="closed"#comment',
        'X="closed" junk',
        "X=it's",
        'X=a"b',
        'X="one\ntwo"',
        "X=one\rY=two",
        "X=\x00secret",
        "X=\x1bsecret",
        "X=\x7fsecret",
    ],
)
def test_rejects_ambiguous_or_unsafe_input(text: str) -> None:
    with pytest.raises(InputError) as caught:
        parse_dotenv(text)
    assert caught.value.issue.code == "dotenv.syntax"
    assert caught.value.issue.line == 1
    assert "secret" not in str(caught.value)


def test_duplicate_assignment_is_not_silently_overwritten() -> None:
    with pytest.raises(InputError) as caught:
        parse_dotenv("X=first\nexport X=second")
    assert caught.value.issue.code == "dotenv.duplicate"
    assert caught.value.issue.line == 2


def test_shell_expressions_are_literal() -> None:
    assert parse_dotenv("A=${TOKEN}\nB=$(touch /tmp/never-run)\nC=`command`") == {
        "A": "${TOKEN}",
        "B": "$(touch /tmp/never-run)",
        "C": "`command`",
    }


@given(st.text(alphabet=st.characters(whitelist_categories=("L", "N")), max_size=150))
def test_quoted_unicode_values_round_trip(value: str) -> None:
    assert parse_dotenv(f'VALUE="{value}"') == {"VALUE": value}
