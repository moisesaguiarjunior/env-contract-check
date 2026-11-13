"""A strict, literal, single-line dotenv grammar; never evaluates shell syntax."""

import re

from env_contract_check.contract import NAME_PATTERN
from env_contract_check.model import InputError, Issue


def _error(code: str, message: str, line: int) -> InputError:
    return InputError(Issue(code, message, line=line))


def _value(text: str, line: int) -> str:
    if not text:
        return ""
    if text[0] in "\"'":
        quote = text[0]
        end = text.find(quote, 1)
        if end < 0:
            raise _error("dotenv.syntax", "Unclosed quote; multiline values are unsupported.", line)
        suffix = text[end + 1 :]
        if suffix and (suffix[0] not in " \t" or not suffix.strip().startswith("#")):
            raise _error(
                "dotenv.syntax", "Only a whitespace-separated comment may follow a quote.", line
            )
        return text[1:end]
    value = re.split(r"[ \t]+#", text, maxsplit=1)[0].rstrip(" \t")
    if "'" in value or '"' in value:
        raise _error(
            "dotenv.syntax", "Quote the entire value; embedded bare quotes are unsupported.", line
        )
    return value


def parse_dotenv(text: str) -> dict[str, str]:
    """Parse literal assignments, rejecting duplicate names and malformed lines.

    No interpolation, escaping, multiline values, or mutation of os.environ.
    """
    values: dict[str, str] = {}
    for number, raw in enumerate(text.removeprefix("\ufeff").split("\n"), start=1):
        raw = raw.removesuffix("\r")
        if any((ord(char) < 32 and char != "\t") or ord(char) == 127 for char in raw):
            raise _error("dotenv.syntax", "Control characters are unsupported.", number)
        line = raw.strip(" \t")
        if not line or line.startswith("#"):
            continue
        if line.startswith(("export ", "export\t")):
            line = line[6:].lstrip(" \t")
        name, separator, value = line.partition("=")
        name = name.rstrip(" \t")
        if not separator or not NAME_PATTERN.fullmatch(name):
            raise _error(
                "dotenv.syntax", "Expected NAME=value with a portable variable name.", number
            )
        if name in values:
            raise _error("dotenv.duplicate", "Duplicate variable assignment.", number)
        values[name] = _value(value.strip(" \t"), number)
    return values
