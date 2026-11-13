# GitHub Action: validate a generated environment before deploying

The root `action.yml` is a composite GitHub Action. It invokes the same CLI and validation core; it does not implement another validator. Typical order:

```text
push a release tag -> generate .env -> validate contract -> deploy that same file
                                             |
                                      failure stops deploy
```

## Availability

The Action is implemented locally and has not been published or run on GitHub-hosted runners. In a checkout of this repository, use `uses: ./`. After publishing, consumers can use `moisesaguiarjunior/env-contract-check@<reviewed-commit-sha>`. Replace the placeholder with a real reviewed commit; no release tag or Marketplace listing currently exists.

The Action installs uv using a pinned upstream action, then runs this checkout with the selected Python version (3.13 by default) in an isolated environment. It does not install into or sync the consumer's Python environment. First-run toolchain/build setup may access GitHub/PyPI; configuration validation itself performs no network requests. Linux runners are the initial workflow target. The exact Bash validation step is also tested locally; that does not emulate the full GitHub runner.

## Inputs

| Input | Default | Meaning |
| --- | --- | --- |
| `contract` | `env.contract.toml` | TOML contract path |
| `env-file` | Required | Generated file to validate |
| `example-file` | Omitted | Optional example-key drift check |
| `strict` | `'false'` | `'true'` rejects undeclared names in the generated file |
| `format` | `text` | `text` or `json` |
| `python-version` | `3.13` | Python 3.11+ runtime used only for the isolated validator |

Paths resolve in the caller's working directory, not the Action source directory. Input strings are passed through environment variables and quoted Bash arrays, not interpolated into executable shell text. No configuration values are sent to the Action as inputs: it reads the already-generated file.

Validation exits 0, 1, or 2 with the [CLI protocol](cli.md). A nonzero result fails the step. Invalid Action boolean input fails with a fixed error message. Setup failures also stop the job. This Action does not require write permissions, upload artifacts, write GitHub outputs, or print the file contents.

## Tag-triggered deployment

[Copyable consumer template](../examples/workflows/deploy-on-tag.yml): replace `REVIEWED_COMMIT_SHA`, supply the contract/example, configure `DEPLOY_ENV`, and replace `./scripts/deploy.sh` with your actual deploy command. Keep validation immediately before deployment and deploy the same file without regenerating it.

The template runs on pushed tags matching `v*`. It uses a `production` environment, writes the environment secret without shell interpolation, validates the file, deploys, and removes the file even on failure. Configure your own environment protections and deployment permissions as needed; the template grants only repository read access and does not define cloud authentication.

Do not use `continue-on-error: true` on the validation gate or `if: always()` on the deployment step: either can bypass failure blocking. `always()` is appropriate for cleanup. Separate jobs require a successful dependency and careful handling of the exact validated configuration; the simple same-job example avoids that extra transfer.

## Local verification

Tests execute the actual Bash `run` block from `action.yml` with uv, a temporary consumer working directory, and synthetic inputs. They cover success, invalid/missing files, example drift, strict mode, paths containing spaces and shell expressions, invalid input values, and a simulated deployment step that must remain unexecuted after failure.

The local test harness skips on Windows where Bash/uv integration has not been verified; the CLI itself still has Windows CI configuration. A dedicated hosted `action-smoke` job is prepared in the CI workflow but has not run.

References reviewed 2026-11-13: [GitHub composite actions](https://docs.github.com/en/actions/tutorials/create-actions/create-a-composite-action), [workflow syntax and failure behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
