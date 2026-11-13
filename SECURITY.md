# Security boundaries

The CLI reads configuration values in memory but omits their contents from expected text and JSON diagnostics. It also omits input paths and raw parser exceptions. Validated variable names, issue codes, and line numbers are intentionally visible. Do not store secrets in variable names.

Dotenv input is never executed, interpolated, or loaded into `os.environ`. No network requests, telemetry, file edits, subprocesses, or plugin loading occur during validation. Reports are not proof that the underlying application configuration is secure: URL checks do not establish trusted hosts, approved schemes, reachability, or authorization.

The process is not a sandbox. File inputs may reference paths accessible to the caller; do not run untrusted commands or grant unnecessary filesystem access. File size limits do not guarantee protection against all resource exhaustion. Library callers must enforce their own input limits. Memory is not securely erased, and debuggers, crash dumps, environment managers, and surrounding shell/CI scripts may expose data independently.

The documented dotenv subset differs from loaders that support interpolation or escape decoding. Validate the resolved process environment if your application's loader transforms values.

## Reporting

Report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/moisesaguiarjunior/env-contract-check/security/advisories/new). Include a minimal synthetic reproducer and affected version. Do not post security findings in public issues or include real `.env` files, tokens, private hostnames, or customer data.
