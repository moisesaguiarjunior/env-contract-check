# Changelog

## 0.1.0 — 2026-11-13

### Added

- Typed TOML environment schema, literal dotenv parsing, and explicit process-environment validation.
- Required/optional variables, integer bounds, string choices, and example-key drift checks.
- Value-free text/JSON diagnostics with documented exit codes.
- Composite GitHub Action and tag-triggered deployment template.
- Agent integration guide, report JSON Schema, and Python API.

### Fixed during local review

- Pin setup-uv to its verified commit object rather than the annotated tag object.
- Preserve leading hash characters in unquoted values instead of silently treating them as empty.
- Handle buffered closed stdout pipes with exit 2 and no shutdown traceback.
- Handle the Windows EINVAL variant of a closed output pipe, confirmed by hosted CI.
