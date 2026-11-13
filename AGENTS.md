# Contributor instructions

This repository is an English-language Python CLI and library. Keep implementation, documentation, comments, and commit messages in English.

## Scope and workflow

- Current authorization is local implementation and verification only. Do not create remotes, push, publish packages, deploy, or send project data to third parties without an explicit request.
- Read `docs/reuso.md` and search for equivalent code before adding a solution. Record what you reused and created. Keep the reuse map current.
- Keep validation pure. Put process/environment/filesystem access in the CLI adapter. Prefer functions and immutable data over speculative interfaces or layers.
- Treat the versioned contract and JSON report as public interfaces. Keep the reference, examples, schema, and behavior tests synchronized.
- Diagnostics must not contain input values, source lines, paths, or exception strings from parsers. Variable names are intentionally visible after identifier validation.
- Never execute or expand dotenv contents. Never silently merge sources or overwrite assignments.
- Do not add global lint/type suppressions, replace failures with success, or weaken tests to satisfy checks.
- Do not commit machine/device identifiers, absolute local paths, user-directory names, raw environment dumps, real credentials, or personal data in evidence. Use synthetic fixtures.
- Preserve other contributors' changes. Close any temporary sessions you create.
- Independent review is separate from author checks and is required before publication. Do not launch other agents automatically or call self-review independent.

## Verify

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest --cov --cov-report=term-missing
uv build --no-sources
uv run --locked twine check dist/*
```

Also install the built wheel into a fresh temporary virtual environment and run both passing and failing examples outside the source checkout. Verify local Markdown links and packaged files when documentation or packaging changes. Report actual checks and untested environments honestly.
