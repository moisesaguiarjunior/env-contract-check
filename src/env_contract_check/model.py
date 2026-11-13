"""Immutable contract and report types; diagnostics never retain input values."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class Kind(StrEnum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    URL = "url"


@dataclass(frozen=True, slots=True)
class Rule:
    name: str
    kind: Kind
    required: bool = True
    allow_empty: bool = False
    minimum: int | None = None
    maximum: int | None = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Contract:
    rules: tuple[Rule, ...]


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    message: str
    variable: str | None = None
    line: int | None = None


class InputError(ValueError):
    """An expected input failure with a safe, structured diagnostic."""

    def __init__(self, issue: Issue) -> None:
        self.issue = issue
        super().__init__(issue.message)


@dataclass(frozen=True, slots=True)
class Report:
    status: Literal["valid", "invalid", "error"]
    checked: int
    issues: tuple[Issue, ...] = ()

    @property
    def exit_code(self) -> int:
        return {"valid": 0, "invalid": 1, "error": 2}[self.status]
