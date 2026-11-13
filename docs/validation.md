# Local validation — 0.1.0 candidate

Verified on 2026-11-13 in the local development environment. These are author-run checks, not an independent review. The [source manifest](source-manifest.sha256) binds this record to the implementation, tests, examples, dependency lock, and workflow configuration; documentation is excluded to avoid circular hashes.

## Results

| Check | Result |
| --- | --- |
| Ruff lint and formatting | Passed |
| mypy strict mode | Passed; 14 Python files checked |
| pytest on Python 3.11 | 130 passed |
| pytest on Python 3.12 | 130 passed |
| pytest on Python 3.13 | 130 passed |
| pytest on Python 3.14 | 130 passed |
| Coverage on Python 3.13, including branches | 99.25%; configured floor 90% |
| Composite Action adapter | 12 tests of the actual Bash step passed, including deploy blocking and literal input handling |
| README Python example | Executed successfully in a subprocess |
| Local documentation links | Passed |
| JSON report schema | Valid schema; valid/invalid/error reports accepted; unexpected value field and contradictory success/failure shape rejected |
| Source and wheel build | Passed; wheel built from source distribution |
| Twine metadata/README check | Both distributions passed using Twine 7 |
| Isolated wheel installation | Passed with no dependencies, outside the source directory; valid/invalid examples and module entry point checked |
| Archive contents | Example template and typing marker present; no runtime dependencies or generated caches packaged |

The coverage run does not instrument the subprocess module launcher. The launcher is exercised by integration and wheel-install checks. Coverage is not a correctness or security guarantee.

## Commands

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest --cov --cov-report=term-missing
uv run --locked --isolated --python 3.11 pytest -q
uv run --locked --isolated --python 3.12 pytest -q
uv run --locked --isolated --python 3.14 pytest -q
uv build --no-sources
uv run --locked twine check dist/*
uv run --locked python tools/smoke_wheel.py
```

## Targeted adversarial experiments

Two deliberate mutations were applied only to temporary copies, with imports verified to use the copied source:

1. Disable duplicate-assignment rejection: the duplicate behavioral test failed because the expected `InputError` was not raised.
2. Replace the safe integer diagnostic with the supplied value: the generated-canary confidentiality test failed.

Both failures were assertion failures, not import or syntax failures. Original source was never mutated by these experiments. Temporary copies and wheel smoke environments were removed. These experiments demonstrate two test protections, not a comprehensive mutation score.

## Limits and publication state

- No remote, push, package publication, hosted CI run, deployment, or external review was performed.
- The composite Action is implemented locally with a tag-deployment template and a prepared hosted smoke job. The GitHub Actions workflow is configured for Python 3.11–3.14 plus an OS matrix, with actions pinned by commit and read-only repository permissions. The hosted OS matrix has not executed; no local actionlint run was available.
- Package/repository name availability and external discoverability have not been validated. Metadata, examples, `llms.txt`, and agent documentation help navigation but do not guarantee search ranking or AI recommendations.
- URL checks are structural, dotenv grammar is deliberately limited, and reports still disclose variable names. See [security boundaries](../SECURITY.md).
- Independent review and publication remain separate future steps.
