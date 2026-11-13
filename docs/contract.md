# Environment contract reference

Contract version: **1**. Format: TOML. Encoding for CLI files: UTF-8, with an optional BOM.

## Root fields

| Field | Required | Meaning |
| --- | --- | --- |
| `version` | Yes | The integer `1`; booleans and strings are rejected |
| `variables` | Yes | A nonempty table of variable definitions |

Variable names are case-sensitive and match `[A-Za-z_][A-Za-z0-9_]*`.
Unknown fields, duplicate TOML keys, and invalid combinations are errors. Rules and reports use alphabetical name order for deterministic output.

## Variable fields

| Field | Default | Applies to | Meaning |
| --- | --- | --- | --- |
| `type` | Required | All | `string`, `integer`, `boolean`, or `url` |
| `required` | `true` | All | Missing names fail; `false` permits absence, not invalid present values |
| `allow_empty` | `false` | String only | Permit the exact empty string |
| `min` | No bound | Integer only | Inclusive lower bound |
| `max` | No bound | Integer only | Inclusive upper bound |
| `choices` | No restriction | String only | Nonempty array of unique allowed strings; exact comparison |

An empty choice requires `allow_empty = true`. Bounds must be integers (not booleans), and `min <= max`. There are no defaults, coercion into application settings, regex validators, secret fields, nested objects, or external includes in version 1.

## Types

- **String:** any nonempty string by default. Whitespace-only strings count as nonempty. Optional choices are case-sensitive. Quoted and process values are not trimmed.
- **Integer:** ASCII decimal digits, optional leading `+` or `-`, at most 640 digits excluding the sign. Leading zeros are accepted. Spaces, separators, decimal points, Unicode digits, and exponential notation are rejected. The digit limit avoids interpreter-dependent conversion limits and excessive work.
- **Boolean:** `true`, `false`, `1`, or `0`; letter case is ignored. `yes`, `on`, and surrounding whitespace are rejected.
- **URL:** a structurally absolute URL with a scheme and host. If supplied, the numeric port must be in `1..65535`. Whitespace, control characters, backslashes, invalid percent escapes, and malformed bracketed hosts fail. Scheme/host allowlists, full RFC conformance, IDNA/DNS validity, reachability, and credential safety are outside this check.

## Dotenv syntax

This is a deliberately limited grammar, not a drop-in parser for every dotenv implementation.

```dotenv
# Full-line comment
PORT=8080
export DEBUG=false
APP_MODE = development # Whitespace-separated comment
API_URL=https://example.com/#fragment
TEXT="spaces and # are literal inside quotes"
OTHER='double "quotes" can be inside single quotes'
EMPTY=
```

- LF and CRLF line endings are accepted. Blank lines and leading/trailing spaces or tabs around assignments are ignored.
- A variable must be assigned with `=`. Bare names are rejected. Duplicate assignments fail instead of silently choosing a winner.
- Single or double quotes must enclose the entire value on one line. After the closing quote, only a whitespace-separated comment is accepted.
- In unquoted values, `#` starts a comment only after a value when preceded by a space/tab. A leading `#` is literal, even after spaces following `=`: `TOKEN=#value` and `TOKEN= #value` both preserve `#value`. Quote values when moving between different dotenv dialects.
- Backslashes and dollar expressions are literal: no escape decoding, interpolation, command substitution, or shell execution occurs. A quote cannot be escaped with a backslash; use the other quote style if appropriate.
- ASCII control characters other than tabs and line endings are rejected, including NUL, ESC, and DEL.

If your application's dotenv loader expands variables or decodes escapes, file validation may inspect a different value than your application uses. Validate the final resolved process environment with `--process-env` when that is the intended contract.

## Example drift

`--example-file` parses the same dotenv grammar but compares only names. Every declared variable, including optional ones, must appear. Undeclared example names fail. Empty or non-typed placeholders are accepted. Source values are never filled from the example.

## Library boundary

`parse_contract(text)` and `parse_dotenv(text)` validate their respective formats. `validate(contract, values, strict=False, example=None)` takes a parsed contract and mappings of strings. It does not mutate the mappings or read process state. Parsing errors raise `InputError`; environment violations return `Report(status="invalid", ...)`.

The 1 MiB input limit belongs to the CLI file adapter. Callers loading library input are responsible for their own size limits and trusted execution environment.
