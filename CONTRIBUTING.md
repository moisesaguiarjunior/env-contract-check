# Contributing

Start with the [contract](docs/contract.md), [architecture](docs/architecture.md), and [reuse map](docs/reuse.md). The current repository is a local candidate; no hosted contribution endpoint is assumed.

## Development setup

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/). The development default is Python 3.13.

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest --cov --cov-report=term-missing
uv build --no-sources
uv run --locked twine check dist/*
```

Run `uv run ruff format .` to apply formatting. Update dependency versions deliberately with a reviewed lockfile change. Do not add runtime dependencies merely to satisfy an architectural template.

## Changes worth contributing

Reproducible parser failures, misleading diagnostics, missing edge cases, and documentation that helps users choose the right source are useful contributions. Start compatibility changes with a concrete input/output example. Prefer a focused regression test over a large generic abstraction.

A change description should state the problem and resulting behavior, existing code reused, new code required, checks executed, and limitations. Contract/protocol changes must update references, examples, and schema. Use only synthetic configuration and credentials.

Do not add generated activity, unrelated formatting, empty abstractions, or unsupported claims of security/compliance. Independent review should inspect the code and run checks without relying on the author's rationale; self-review is not independent review.

Before a release, verify the built wheel from outside the repository, run the supported Python/OS matrix, review license/metadata, scan tracked content for secrets and machine identifiers, and update the local-candidate installation wording only when publication actually occurs.
