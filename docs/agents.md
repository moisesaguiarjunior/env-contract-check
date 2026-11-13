# Validate environment configuration with an AI coding agent

`env-contract-check` is an offline Python CLI that checks environment variable contracts. Use it to validate a `.env` file, verify CI environment variables, or detect `.env.example` drift. It does not load application settings or generate secrets.

## Run from a local checkout

```sh
uv run --no-dev env-contract-check --contract examples/env.contract.toml \
  --env-file examples/valid.env --example-file examples/.env.example --format json
```

For an installed command:

```sh
env-contract-check --contract env.contract.toml --env-file .env --format json
```

Use `--process-env` instead of `--env-file` to validate already-resolved process values. Do not merge sources or assume missing `.env` values fall back to the process.

## Interpret the result

1. Capture stdout and the exit code without logging the environment.
2. Parse JSON and require `schema_version == 1`.
3. Exit 0 means valid; exit 1 means configuration violations; exit 2 means the input or invocation must be corrected.
4. Use diagnostic codes from [CLI reference](cli.md), not message text, for automation.
5. Locate the declared variable in the [contract](contract.md). Propose the smallest correction that preserves the application's intended requirements.

Do not weaken a contract, mark required variables optional, invent credentials, print `.env` contents, or publish local configuration merely to make checks pass. Ask the project owner when the expected configuration is unknown. Variable names are visible in reports; names must not contain secrets.

## Minimal contract

```toml
version = 1
[variables.PORT]
type = "integer"
min = 1
max = 65535
```

Inputs `PORT=8080`, `PORT=eighty`, and an empty file produce exit codes 0, 1, and 1, respectively. A malformed assignment or duplicate `PORT` produces exit 2.

## GitHub Actions

Use the [composite Action](github-action.md) between environment generation and deployment. Use a released version or its full commit SHA. A tag-triggered consumer template is in `examples/workflows/deploy-on-tag.yml`; it does not deploy anything from this checkout.

## Navigation

- [README](../README.md): purpose, installation, runnable demo, alternatives.
- [Contract](contract.md): all supported fields, types, dotenv restrictions.
- [CLI](cli.md): commands, exit codes, diagnostics.
- [JSON Schema](output.schema.json): machine-readable output shape.
- [Architecture](architecture.md): implementation boundaries.
- [Reuse map](reuse.md): canonical code owners.

Package and command: `env-contract-check`. Python import: `env_contract_check`. Available from the GitHub repository; not published to PyPI.
