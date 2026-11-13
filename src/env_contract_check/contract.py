"""Parse the closed, versioned TOML contract into immutable rules."""

import re
import tomllib

from env_contract_check.model import Contract, InputError, Issue, Kind, Rule

NAME_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)
_ROOT_FIELDS = {"version", "variables"}
_RULE_FIELDS = {"type", "required", "allow_empty", "min", "max", "choices"}


def _error(message: str, name: str | None = None) -> InputError:
    return InputError(Issue("contract.invalid", message, variable=name))


def _boolean(data: dict[str, object], key: str, default: bool, name: str) -> bool:
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise _error(f"'{key}' must be a boolean.", name)
    return value


def _bound(data: dict[str, object], key: str, name: str) -> int | None:
    value = data.get(key)
    if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
        raise _error(f"'{key}' must be an integer.", name)
    return value


def _rule(name: str, data: object) -> Rule:
    if not isinstance(data, dict) or set(data) - _RULE_FIELDS:
        raise _error("Expected a variable table with documented fields only.", name)
    kind_value = data.get("type")
    if not isinstance(kind_value, str):
        raise _error("'type' must be string, integer, boolean, or url.", name)
    try:
        kind = Kind(kind_value)
    except (ValueError, TypeError):
        raise _error("'type' must be string, integer, boolean, or url.", name) from None
    required = _boolean(data, "required", True, name)
    allow_empty = _boolean(data, "allow_empty", False, name)
    minimum, maximum = _bound(data, "min", name), _bound(data, "max", name)
    if ("min" in data or "max" in data) and kind != Kind.INTEGER:
        raise _error("Bounds are supported only for integer variables.", name)
    if minimum is not None and maximum is not None and minimum > maximum:
        raise _error("'min' must not exceed 'max'.", name)
    if "allow_empty" in data and kind != Kind.STRING:
        raise _error("'allow_empty' is supported only for string variables.", name)
    choices = data.get("choices", [])
    if not isinstance(choices, list) or not all(isinstance(item, str) for item in choices):
        raise _error("'choices' must be an array of strings.", name)
    if "choices" in data and (kind != Kind.STRING or not choices):
        raise _error("'choices' requires a string variable and a nonempty array.", name)
    if len(set(choices)) != len(choices) or ("" in choices and not allow_empty):
        raise _error("Choices must be unique; an empty choice requires allow_empty.", name)
    return Rule(name, kind, required, allow_empty, minimum, maximum, tuple(choices))


def parse_contract(text: str) -> Contract:
    """Parse contract version 1. Reject unknown fields and ambiguous configuration."""
    try:
        data = tomllib.loads(text)
    except (ValueError, RecursionError):
        raise _error("Invalid TOML. Check the contract syntax.") from None
    if set(data) - _ROOT_FIELDS:
        raise _error("Unknown root fields; only version and variables are supported.")
    if type(data.get("version")) is not int or data["version"] != 1:
        raise _error("'version' must be the integer 1.")
    variables = data.get("variables")
    if not isinstance(variables, dict) or not variables:
        raise _error("'variables' must contain at least one variable table.")
    rules = []
    for name, definition in sorted(variables.items()):
        if not NAME_PATTERN.fullmatch(name):
            raise _error("Variable names must match [A-Za-z_][A-Za-z0-9_]*.")
        rules.append(_rule(name, definition))
    return Contract(tuple(rules))
