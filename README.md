<div align="center">

# env-contract-check

### Catch configuration mistakes before your application starts.

**Validate `.env` files and environment variables against a typed contract.**
Find missing variables, invalid values, and stale `.env.example` files — with reports that omit values.

**Python 3.11+ · Zero runtime dependencies · Offline · CI-ready JSON · GitHub Action**

[Quick start](#quick-start) · [Contract reference](docs/contract.md) · [GitHub Action](docs/github-action.md) · [CLI & JSON](docs/cli.md) · [For AI agents](docs/agents.md) · [Contributing](CONTRIBUTING.md)

</div>

```text
$ env-contract-check --contract examples/env.contract.toml --env-file examples/invalid.env

INVALID: 3 issue(s).
  [value.url] API_URL: Expected an absolute URL with a host and valid port.
  [value.boolean] DEBUG: Expected true, false, 1, or 0 (case-insensitive).
  [value.integer] PORT: Expected a decimal integer of at most 640 digits.
```

**Status:** local development candidate, version `0.1.0`. Not published to PyPI. The commands below install or run this checkout. CI is defined, but no hosted CI result or independent review is claimed.

## Why an environment contract?

Your application needs a numeric port, a URL, and a handful of required settings. A `.env.example` lists names, but cannot reliably express those rules. A deployment can contain every name and still fail because `PORT=eighty`.

`env-contract-check` makes those expectations explicit in a small TOML file. Run the same check on a local `.env` or on the environment supplied by your CI runner. The application can be written in Python, JavaScript, or any other language; Python is required only to run this validator.

| Catch | Example | Report code |
| --- | --- | --- |
| Missing required configuration | `API_URL` is absent | `value.missing` |
| Empty configuration | `API_URL=` | `value.empty` |
| Invalid types | `PORT=eighty` | `value.integer` |
| Values outside allowed bounds | Port exceeds the contract maximum | `value.range` |
| Unexpected choices | Mode is not an allowed string | `value.choice` |
| Undocumented or stale example keys | Contract and `.env.example` disagree | `example.missing` / `example.unexpected` |
| Duplicate assignments | Two definitions of the same variable | `dotenv.duplicate` |
| Contract typos | `requried` instead of `required` | `contract.invalid` |

## Quick start

From this checkout, with [uv](https://docs.astral.sh/uv/):

```sh
uv run --no-dev env-contract-check \
  --contract examples/env.contract.toml \
  --env-file examples/valid.env \
  --example-file examples/.env.example \
  --strict
```

```text
PASS: 4 declared variables checked.
```

To install a standalone local command:

```sh
uv tool install .
```

Or, inside an activated Python 3.11+ virtual environment:

```sh
python -m pip install .
```

Create `env.contract.toml`:

```toml
version = 1

[variables.API_URL]
type = "url"

[variables.PORT]
type = "integer"
min = 1
max = 65535

[variables.DEBUG]
type = "boolean"
required = false

[variables.APP_MODE]
type = "string"
choices = ["development", "test", "production"]
```

Then validate your own file:

```sh
env-contract-check --contract env.contract.toml --env-file .env
```

All variables are required and nonempty unless explicitly configured otherwise. Optional variables are still validated when present. See the [complete contract](docs/contract.md).

## GitHub Action: block deployment on a bad `.env`

Push a release tag, generate the deployment environment, validate it, and deploy **the same file only if validation succeeds**.

```text
Tag v1.2.3 -> generate .env -> validate contract -> deploy
                                    |
                             invalid: job fails
```

The reusable composite Action is implemented in [action.yml](action.yml). It forwards inputs to the same CLI in an isolated Python environment. **It is still local:** the consumer template below becomes usable after publication. Replace `REVIEWED_COMMIT_SHA` with the reviewed public commit and replace the deploy command with your own script.

```yaml
# Consumer template: replace REVIEWED_COMMIT_SHA and the deploy command before use.
# This file is documentation; it is not an active workflow in this repository.
name: Validate environment and deploy

on:
  push:
    tags: ['v*']

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803 # v6
        with:
          persist-credentials: false
      - name: Write generated environment
        shell: python
        env:
          DEPLOY_ENV_CONTENT: ${{ secrets.DEPLOY_ENV }}
        run: |
          import os
          from pathlib import Path
          Path('.env.deploy').write_text(os.environ['DEPLOY_ENV_CONTENT'], encoding='utf-8')
      - name: Validate before deployment
        uses: moisesaguiarjunior/env-contract-check@REVIEWED_COMMIT_SHA
        with:
          contract: env.contract.toml
          env-file: .env.deploy
          example-file: .env.example
          strict: 'true'
      - name: Deploy the validated file
        run: ./scripts/deploy.sh .env.deploy
      - name: Remove generated environment
        if: always()
        shell: python
        run: |
          from pathlib import Path
          Path('.env.deploy').unlink(missing_ok=True)
```

`DEPLOY_ENV` is the complete dotenv content supplied by your deployment configuration/secret generator. You can replace the write step with your existing generation step. Missing or invalid settings fail validation; the following deployment step does not run. Do not add `continue-on-error` to the validation gate or regenerate the file between validation and deployment.

For a checkout of this tool itself, the Action can be referenced locally with `uses: ./`. See [Action inputs, local tests, and integration boundaries](docs/github-action.md).

## Check configuration in CI

Validate the environment already provided by your runner:

```sh
env-contract-check --contract env.contract.toml --process-env --format json
```

Or check a file and its example together:

```sh
env-contract-check --contract env.contract.toml --env-file .env \
  --example-file .env.example --format json
```

| Exit code | Meaning |
| --- | --- |
| `0` | Validation passed |
| `1` | Environment or example violates the contract |
| `2` | Invalid arguments, unreadable input, or invalid contract/dotenv syntax |

JSON reports go to stdout, including expected input errors. Diagnostics have stable codes, variable names, and optional line numbers. They omit input values, source lines, and paths. Use `schema_version` and diagnostic codes for automation; message prose may evolve. See the [output schema](docs/output.schema.json).

`--strict` rejects undeclared names. Leave it off for normal process environments, which also contain variables such as `PATH`.

## Predictable input, explicit limits

- **One source at a time.** Choose `--env-file` or `--process-env`. No automatic search, fallback, merging, or modification of `os.environ`.
- **Literal dotenv subset.** Single-line `NAME=value` assignments, optional `export`, whole-value quotes, and comments. No interpolation, escape decoding, shell execution, or multiline values. `$NAME` and `${NAME}` remain literal text. [Syntax and compatibility](docs/contract.md#dotenv-syntax).
- **Examples document names.** Example keys must exactly match all contract keys, including optional ones. Placeholder values are not type-checked.
- **No network checks.** URL validation checks structure; it does not check DNS, reachability, trusted hosts, or allowed schemes.
- **No secret-scanning claim.** Reports expose variable names and diagnostic metadata. Do not put secrets in names. The tool reads values in memory; it is not a vault, redactor for other logs, or a sandbox. [Security boundaries](SECURITY.md).
- **Bounded files.** CLI inputs must be UTF-8 and at most 1 MiB each. The library accepts already-loaded strings.

## When to use this instead of an alternative

| Tool | Best fit |
| --- | --- |
| **env-contract-check** | A language-independent, explicit contract checked before startup, with value-free text/JSON diagnostics and example-key checks |
| [python-dotenv](https://bbc2.github.io/python-dotenv/) | Loading dotenv configuration, including richer syntax and variable expansion |
| [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Typed application settings integrated into Python code |
| [dotenv-linter](https://github.com/dotenv-linter/dotenv-linter) | Linting dotenv files for formatting and common mistakes |

If application settings already give you the checks you need, keep using them. This tool is useful when you want an explicit preflight contract shared across applications or deployment scripts. Comparison reviewed on 2026-11-13; it is not an exhaustive feature audit.

## Python API

```python
from env_contract_check import parse_contract, parse_dotenv, validate

contract = parse_contract("""
version = 1
[variables.PORT]
type = "integer"
min = 1
max = 65535
""")
values = parse_dotenv("PORT=8080")
report = validate(contract, values)
assert report.exit_code == 0
```

Parsing raises `InputError` for expected input failures. Validation returns an immutable report and does not perform I/O. Build contracts with `parse_contract`; model constructors are data containers, not an alternative validation boundary.

## For AI coding agents

Use [the agent integration guide](docs/agents.md) for executable examples, exit-code handling, and safe remediation. [llms.txt](llms.txt) is a compact documentation index; [AGENTS.md](AGENTS.md) contains contributor instructions. Neither file guarantees indexing or recommendations by search engines or AI systems.

Useful discovery terms: **dotenv validator**, **environment variable validation**, **environment configuration contract**, **`.env.example` drift detection**, **CI configuration preflight**, **Python CLI**.

## Development

```sh
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
uv run --locked pytest --cov --cov-report=term-missing
uv build --no-sources
uv run --locked twine check dist/*
```

Tests cover source isolation, malformed files, duplicate variables, type boundaries, example drift, JSON output, and generated secret canaries. See [architecture](docs/architecture.md), [reuse map](docs/reuso.md), and [local validation evidence](docs/validation.md).

## License

[MIT](LICENSE).
