# Architecture and decisions

Implementation decisions for the local 0.1.0 candidate, 2026-11-13. These choices implement the requested scope; they are not independent review findings or publication approval.

## Data flow

```text
TOML text -> parse_contract -> immutable Contract
.env text -> parse_dotenv   -> mapping of strings
                               |
Contract + mapping + optional example keys -> validate -> immutable Report
                                                            |
                                                   text or JSON output
```

`cli.py` owns file reads, environment snapshots, arguments, and output. The parser and validator do not know the filesystem, process environment, terminal, or network. Model objects contain the contract and safe findings; a report never retains the evaluated values.

The composite `action.yml` forwards explicit inputs to the same CLI in an isolated environment. It adds no validation logic. This is a functional core with thin adapters, not a framework of interchangeable layers. Parsing validates the external contract before the validator receives it. Model constructors are data containers and are not a second contract parser.

## Reuse considered before implementation

Searched the Apps Lab repository for environment, dotenv, Python project configuration, and reuse maps. There was no existing implementation of this contract to reuse. This is a new, separate repository; its initial reuse map did not previously exist.

Reviewed these primary references on 2026-11-13:

- [python-dotenv](https://bbc2.github.io/python-dotenv/): a broader dotenv loader with interpolation support. Its public value-loading interface does not express our strict duplicate/malformed-input diagnostic contract. Depending on parser internals would couple this CLI to a non-public interface.
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): appropriate for Python application settings; unnecessary as a runtime dependency for four types and a neutral external contract.
- [dotenv-linter](https://github.com/dotenv-linter/dotenv-linter): an existing linter, not the typed TOML contract proposed here.
- [tomllib](https://docs.python.org/3.11/library/tomllib.html): reused for TOML parsing; available in Python 3.11+.
- [urllib.parse](https://docs.python.org/3.11/library/urllib.parse.html#url-parsing-security): reused for URL decomposition, with explicit checks because parsing alone does not validate a URL.
- [uv](https://docs.astral.sh/uv/guides/projects/): dependency locking and reproducible development commands.

**Reused:** standard-library TOML parsing, URL decomposition, argument parsing, dataclasses, JSON, and packaging metadata; established development/build/test tools.

**Created:** a closed version 1 contract, a documented single-line literal dotenv subset, deterministic validation, and safe structured reports. The custom dotenv parser is intentionally small and rejects unsupported syntax instead of claiming full compatibility.

## Decisions and consequences

- **Zero runtime dependencies:** standard-library-only installation. Development dependencies are locked separately in `uv.lock`.
- **TOML contract:** readable comments and typed metadata; no execution or import of application code. Unknown fields fail to catch typos.
- **Immutable models:** frozen dataclasses and tuples; no shared mutable rules or global environment state.
- **Explicit source:** file or process, never automatic layering. Applications needing interpolation should validate resolved process values.
- **Safe errors:** parser exception text and paths are discarded at the CLI boundary. Reports retain codes, fixed messages, safe names, and line numbers. The API does not provide secure memory erasure.
- **Stable machine interface:** output schema version 1, three exit statuses, deterministic ordering. No agent-specific server is needed for a command with JSON output.
- **Bounds:** CLI file reads stop after 1 MiB + 1 byte; integer values are limited to 640 digits. These limits reduce accidental resource abuse, not a sandbox guarantee.
- **Verification:** examples, error cases, subprocess entry points, and property tests. Coverage is a gap detector with a 90% floor, not proof of correctness.

No service, database, telemetry, plugin system, auto-fix, schema inference, or publishing automation is included. Extensions should begin with an actual use case and a compatibility decision.
