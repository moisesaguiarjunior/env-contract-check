# Reuse map

One canonical owner per responsibility. Paths refer to existing implementations.

| Need | Use | Consumer |
| --- | --- | --- |
| Parse and validate contract version 1 | `src/env_contract_check/contract.py::parse_contract` | CLI and Python API |
| Validate portable variable names | `src/env_contract_check/contract.py::NAME_PATTERN` | Contract, dotenv parser, safe unknown-name diagnostics |
| Parse literal dotenv text | `src/env_contract_check/dotenv.py::parse_dotenv` | Environment and example file inputs |
| Represent rules and safe reports | `src/env_contract_check/model.py` | Parsers, validation, renderer |
| Evaluate types, presence, bounds, choices, and example keys | `src/env_contract_check/validation.py::validate` | CLI and Python API |
| Read bounded UTF-8 files and explicit process state | `src/env_contract_check/cli.py` | Console and module entry points |
| Publish measured coverage | `.github/workflows/coverage.yml` | Codecov badge; the local pytest coverage contract remains authoritative |
| Verify remote Action pins | `tools/verify_action_pins.py` and `docs/action-pins.json` | Release verification and offline pin regression |
| Validate a generated file in GitHub Actions | `action.yml` forwards quoted arguments to the CLI | Tag-triggered consumer template and Action tests |
| Serialize the report consistently | `src/env_contract_check/cli.py::render` | CLI and output tests |

Before adding a validator or parser, search these owners and their tests. Environment and example files use the same parser; example values intentionally skip type validation because their purpose is to document names.

Initial search and alternative evaluation are recorded in [architecture](architecture.md). No previous project implementation was copied.
