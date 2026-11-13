# CLI and JSON protocol

```text
env-contract-check --contract PATH (--env-file PATH | --process-env)
                   [--example-file PATH] [--strict] [--format text|json]
```

Also available as `python -m env_contract_check`. `--help` and `--version` exit with 0.
Argument abbreviation is disabled. No implicit files are loaded. Paths resolve relative to the current directory. Inputs are read only; reports do not contain paths or source values.

`--strict` is intended for curated files. With `--process-env`, it also rejects ordinary undeclared process variables such as `PATH` and `HOME`; omit it unless you intentionally validate the entire environment.

## Exit codes and streams

| Code | Status | Meaning |
| --- | --- | --- |
| 0 | `valid` | All applicable checks passed |
| 1 | `invalid` | Environment/example violations |
| 2 | `error` | Usage, file access, parsing, or contract failure |

Reports go to stdout in both formats. Expected errors do not print tracebacks. Broken output pipes return 2. Unexpected programming/runtime failures are not disguised as a successful report. Help/version output is plain text, including when `--format json` is present.

```json
{
  "schema_version": 1,
  "status": "invalid",
  "checked": 1,
  "issues": [
    {
      "code": "value.missing",
      "message": "Set the required variable.",
      "variable": "PORT",
      "line": null
    }
  ]
}
```

`checked` is the number of declared rules considered, including absent optional variables. Input/usage errors report `checked: 0`: no complete validation pass occurred. `issues` is empty on success. Lines are one-based dotenv line numbers; the message identifies whether the syntax error is in the environment file or the example file, without exposing its path.

Output is deterministic for identical input. Rule violations appear alphabetically, followed by strict unknown-name issues, missing example keys, and unexpected example keys. The CLI stops at the first input/parsing failure; semantic validation collects all applicable issues.

## Diagnostic codes

| Code | Meaning |
| --- | --- |
| `cli.arguments` | Invalid or missing arguments; consult `--help` |
| `input.unreadable` | File cannot be read as UTF-8 |
| `input.too_large` | Input exceeds 1 MiB |
| `contract.invalid` | Malformed TOML or invalid contract structure/constraints |
| `dotenv.syntax` | Unsupported or malformed assignment |
| `dotenv.duplicate` | Repeated assignment |
| `value.missing` | Required variable absent |
| `value.empty` | Empty value not allowed |
| `value.integer` | Invalid decimal integer |
| `value.range` | Integer outside contract bounds |
| `value.boolean` | Invalid boolean spelling |
| `value.url` | Invalid structural URL |
| `value.choice` | String outside allowed choices |
| `value.unexpected` | Undeclared source name in strict mode |
| `example.missing` | Declared name missing from example |
| `example.unexpected` | Example name not declared |

Integrate using exit codes, `schema_version`, and issue `code`; do not parse English messages. Variable names are emitted only when they match the portable identifier syntax. Input values, allowed-choice contents, and file paths are not serialized. The [JSON Schema](output.schema.json) defines the version 1 shape. Breaking protocol changes require a schema version change; new diagnostic codes may be added within the current schema.
