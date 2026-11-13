# First independent Sol review

Reviewed on 2026-11-13. Commit: `4b78974e8635c1997495d0c8bd384fb0cb98b979`.

This is an independent, local, read-only review of that commit's implementation. The reviewer did not author or modify the implementation. This report is the only intentional tracked-file addition made during the review. No publication, remote creation, push, deployment, hosted CI execution, or third-party transmission was performed.

## Scope and approach

Started from the requested behavior and the current code: a small Python CLI/API for explicit dotenv or process-environment validation, value-free diagnostics, English documentation useful to people and AI agents, and a reusable GitHub Action that gates deployment after configuration generation. Inspected all Python source and tests, `action.yml`, both workflow files, `pyproject.toml`, dependency lock, examples, README, contributor instructions, reuse map, contract/CLI references, output schema, agent documentation, architecture and security boundaries. Author validation notes were read separately and were not used as evidence of reviewer execution.

Actively searched for duplicate parsing, validation, report rendering and deployment-gate logic. The Action delegates to the CLI; environment and example files use the same parser; portable-name checks use the canonical pattern. The two small unknown-name diagnostic branches are similar, but do not justify another abstraction in this scope. No material duplication finding was identified.

## Findings

### P3 — Buffered stdout bypasses the promised broken-pipe exit code

Location: `src/env_contract_check/cli.py:122`. Relevant test: `tests/test_cli.py:189`.

The `try/except BrokenPipeError` surrounds `print`, but a small report written to a pipe is normally buffered. `print` succeeds, `main` returns, and the interpreter later flushes stdout during shutdown. When the reader has closed the pipe, that flush raises outside the handler. The actual executable exits **120** and emits an exception diagnostic instead of the documented exit **2** with the expected report behavior.

Reproduced against the reviewed commit with a valid one-variable contract and valid dotenv file. A parent process created an OS pipe, closed its read end before launching the actual module, and passed the write end as the child's stdout. Result:

```text
returncode: 120
stderr: Exception ignored on flushing sys.stdout:
        BrokenPipeError: [Errno 32] Broken pipe
```

The existing test replaces `print` with a function that immediately raises, so it cannot detect this real buffering/shutdown case. This is a low-severity CLI protocol failure: deployment remains blocked by a nonzero status, and no configuration value was exposed in this reproduction. It affects consumers that rely on the documented exit-code set or expect clean pipeline handling.

Suggested correction: flush within the protected output operation, then ensure the failed output stream cannot raise again during interpreter shutdown. Add a subprocess regression using a genuinely closed output pipe rather than only monkeypatching `print`.

Sanitized reproduction, from the repository root after development setup:

```sh
UV_OFFLINE=true uv run --locked python - <<'PY'
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory(prefix="env-review-pipe-") as temporary:
    root = Path(temporary)
    contract = root / "contract.toml"
    dotenv = root / "input.env"
    contract.write_text('version=1\n[variables.PORT]\ntype="integer"')
    dotenv.write_text("PORT=8080")
    reader, writer = os.pipe()
    os.close(reader)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "env_contract_check",
             "--contract", str(contract), "--env-file", str(dotenv)],
            stdout=writer, stderr=subprocess.PIPE, text=True, check=False,
        )
    finally:
        os.close(writer)
    print(result.returncode)
    print(result.stderr)
PY
```

No higher-severity finding was confirmed in the reviewed scope.

## Reviewer-executed verification

All dependency/build/test commands below ran with `UV_OFFLINE=true`, using locally available dependencies and toolchains. No online dependency fetch or source lookup was performed.

| Check | Reviewer result |
| --- | --- |
| `uv run --locked ruff check .` | Passed |
| `uv run --locked ruff format --check .` | Passed; 25 files checked |
| `uv run --locked mypy` | Passed; 14 source files checked |
| `uv run --locked pytest --cov --cov-report=term-missing` | 130 passed on Python 3.13; 99.25% branch-inclusive coverage |
| `uv run --locked --isolated --python 3.11 pytest -q` | 130 passed |
| `uv run --locked --isolated --python 3.12 pytest -q` | 130 passed |
| `uv run --locked --isolated --python 3.14 pytest -q` | 130 passed |
| `uv build --no-sources` | Source distribution and wheel built successfully; wheel built from source distribution |
| `uv run --locked twine check dist/*` | Both artifacts passed |
| `uv run --locked python tools/smoke_wheel.py` | Fresh isolated wheel installation, valid/failing examples and module entry point passed outside the checkout; temporary environment removed |
| `shasum -a 256 -c docs/source-manifest.sha256` | All listed files matched |
| Wheel/source archive enumeration | Typing marker/license and intended source-distribution documents/examples present; wheel contains runtime package and metadata, with no runtime dependencies |

The executed test suite includes the actual composite Action Bash block in a separate synthetic consumer directory: successful validation permits a deployment marker; invalid or missing configuration, duplicate assignments, example drift, strict unknown names and invalid inputs prevent it. Literal paths containing spaces and shell expressions remained data. These are local shell tests, not hosted Action runs.

The documentation tests executed the README Python snippet, resolved local documentation links, validated the JSON Schema and checked representative reports. Additional reviewer probes covered malformed bracketed URL authorities on Python 3.11 and 3.13, deliberately invalid path input through the Python CLI function, help handling, archive contents and the real closed-pipe behavior above. Unsupported embedded-NUL paths supplied directly to `main` raise `ValueError`; executable arguments cannot contain NUL, and `main` is not the documented public library validation interface, so this was not promoted to an executable CLI finding.

## Limits and residual risks

- No GitHub-hosted workflow, upstream setup Action, fresh online toolchain bootstrap, Marketplace consumer, Windows execution or other hosted environment was validated. Local suite results do not certify those integrations. No actionlint execution was performed.
- README content, links, examples and structural readability were reviewed; no independent visual approval or browser-rendered layout certification is claimed. Search ranking, name availability and external agent discoverability were not tested.
- The documented structural URL check, literal dotenv subset, visible validated variable names, caller-controlled library size limits and lack of secure memory erasure remain explicit boundaries. The review did not turn those boundaries into stronger security claims.
- No fuzzing campaign beyond the existing property tests and targeted probes, exhaustive mutation testing, online dependency audit or comprehensive denial-of-service assessment was performed.
- Temporary reproducer files and the smoke-test virtual environment were removed automatically; all invoked command sessions completed. Existing user files and implementation were preserved.

This assessment applies to the full commit above, not future fixes. The confirmed P3 requires verification after correction. Passing tests and absence of additional findings do not prove absence of bugs or constitute publication approval.
