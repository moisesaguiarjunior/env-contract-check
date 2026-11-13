"""Pure environment validation; no filesystem, process state, or network access."""

import re
from collections.abc import Mapping
from urllib.parse import urlsplit

from env_contract_check.contract import NAME_PATTERN
from env_contract_check.model import Contract, Issue, Kind, Report, Rule

_INTEGER = re.compile(r"[+-]?[0-9]+", re.ASCII)


def _is_url(value: str) -> bool:
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    if "\\" in value or re.search(r"%(?![0-9a-fA-F]{2})", value):
        return False
    try:
        parts = urlsplit(value)
        # urlsplit is a parser, not a validator. Reading port also checks its range.
        return (
            bool(parts.scheme and parts.hostname and parts.netloc)
            and not parts.netloc.endswith(":")
            and (parts.port is None or 1 <= parts.port <= 65535)
        )
    except ValueError:
        return False


def _check_value(rule: Rule, value: str) -> Issue | None:
    def issue(code: str, message: str) -> Issue:
        return Issue(code, message, rule.name)

    if value == "" and not rule.allow_empty:
        return issue("value.empty", "Set a nonempty value.")
    match rule.kind:
        case Kind.STRING:
            if rule.choices and value not in rule.choices:
                return issue("value.choice", "Use one of the choices in the contract.")
        case Kind.INTEGER:
            if not _INTEGER.fullmatch(value) or len(value.lstrip("+-")) > 640:
                return issue("value.integer", "Expected a decimal integer.")
            number = int(value)
            if (rule.minimum is not None and number < rule.minimum) or (
                rule.maximum is not None and number > rule.maximum
            ):
                return issue("value.range", "Use an integer within the contract bounds.")
        case Kind.BOOLEAN:
            if value.lower() not in {"true", "false", "1", "0"}:
                return issue("value.boolean", "Expected true, false, 1, or 0 (case-insensitive).")
        case Kind.URL:
            if not _is_url(value):
                return issue("value.url", "Expected an absolute URL with a host and valid port.")
    return None


def validate(
    contract: Contract,
    values: Mapping[str, str],
    *,
    strict: bool = False,
    example: Mapping[str, str] | None = None,
) -> Report:
    """Validate a parsed contract against strings, optionally checking exact example keys.

    Optional means absent is allowed; present values still undergo validation.
    Example values are placeholders and are never type-checked.
    """
    issues: list[Issue] = []
    names = {rule.name for rule in contract.rules}
    for rule in contract.rules:
        if rule.name not in values:
            if rule.required:
                issues.append(Issue("value.missing", "Set the required variable.", rule.name))
        elif problem := _check_value(rule, values[rule.name]):
            issues.append(problem)
    if strict:
        for name in sorted(values.keys() - names):
            # External process environments can contain arbitrary, unsafe names.
            safe_name = name if NAME_PATTERN.fullmatch(name) else None
            issues.append(
                Issue("value.unexpected", "Variable is not declared in the contract.", safe_name)
            )
    if example is not None:
        for name in sorted(names - example.keys()):
            issues.append(
                Issue("example.missing", "Document this variable in the example file.", name)
            )
        for name in sorted(example.keys() - names):
            safe_name = name if NAME_PATTERN.fullmatch(name) else None
            issues.append(
                Issue(
                    "example.unexpected",
                    "Example variable is not declared in the contract.",
                    safe_name,
                )
            )
    return Report("invalid" if issues else "valid", len(contract.rules), tuple(issues))
