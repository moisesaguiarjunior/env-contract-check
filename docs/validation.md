# Validation evidence — 0.1.0

The baseline results below were recorded on 2026-11-13 for implementation commit `0a00591` in the local development environment. These are author-run checks; independent reviews are linked separately. The [source manifest](source-manifest.sha256) tracks the current implementation, tests, examples, dependency lock, and workflow configuration; it is updated with source changes and does not extend historical test results to later commits.

## Results

| Check | Result |
| --- | --- |
| Ruff lint and formatting | Passed |
| mypy strict mode | Passed; 15 Python files checked |
| pytest on Python 3.11 | 139 passed |
| pytest on Python 3.12 | 139 passed |
| pytest on Python 3.13 | 139 passed |
| pytest on Python 3.14 | 139 passed |
| Coverage on Python 3.13, including branches | 98.24%; configured floor 90% |
| Composite Action adapter | 12 tests of the actual Bash step passed, including deploy blocking and literal input handling |
| README Python example | Executed successfully in a subprocess |
| Local documentation links | Passed |
| JSON report schema | Valid schema; valid/invalid/error reports accepted; unexpected value field and contradictory success/failure shape rejected |
| Source and wheel build | Passed; wheel built from source distribution |
| Twine metadata/README check | Both distributions passed using Twine 7 |
| Isolated wheel installation | Passed with no dependencies, outside the source directory; valid/invalid examples and module entry point checked |
| Archive contents | Example template and typing marker present; no runtime dependencies or generated caches packaged |

The coverage run does not instrument the subprocess module launcher or its real closed-pipe regression. The launcher is exercised by integration and wheel-install checks. Coverage is not a correctness or security guarantee.

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

## Review corrections

The first Sol review found buffered broken-pipe shutdown behavior; the separate Opus review identified the setup-uv annotated-tag pin and leading-hash value semantics. These were corrected locally with subprocess/parser regressions. The three remote Action pins were verified through GitHub Git commit endpoints using `tools/verify_action_pins.py`; offline regression evidence is in `action-pins.json`. Sol independently reconfirmed the corrections at commit `0a00591`; see the [follow-up review](reviews/followup-review-sol.md). The first report remains bound to its original commit.

## First hosted validation

The [first Checks run](https://github.com/moisesaguiarjunior/env-contract-check/actions/runs/43520383690) on `7bd2935` passed the Linux Python 3.11–3.14 jobs, macOS Python 3.13, and the composite Action's acceptance/rejection checks. Windows exposed an additional closed-pipe variant: `OSError(EINVAL)` rather than `BrokenPipeError`. Commit `fc59647` handles that variant while preserving propagation of unrelated exceptions and retaining both real-pipe regressions unchanged.

Author checks after that correction: 139 tests on Python 3.13, Ruff, formatting, mypy, build, Twine, and isolated installed-wheel checks passed. Combined local coverage was 97.27%; the new exception branch is exercised by subprocesses outside the main coverage instrumentation. Hosted results for each subsequent commit are recorded in the [Checks workflow](https://github.com/moisesaguiarjunior/env-contract-check/actions/workflows/ci.yml); use the exact commit's result when assessing a release.

## Limits

- The Action smoke job validates synthetic files and failure propagation; it does not deploy an application or certify a consumer's deployment configuration.
- No local actionlint run or comprehensive dependency audit was performed.
- URL checks are structural, dotenv grammar is deliberately limited, and reports still disclose variable names. See [security boundaries](../SECURITY.md).
- PyPI distribution and a Marketplace listing are separate from the GitHub repository and release. See the [release process](publishing.md).
