# Release process

The project is distributed through its public GitHub repository, GitHub releases, and composite Action. It is not published to PyPI.

## Before publishing a release

- Reconcile independent review findings against the exact commit to publish.
- Run the documented lint, type, test, build, metadata, and installed-wheel checks.
- Run `uv run --locked python tools/verify_action_pins.py` when changing Action pins. This reads public GitHub metadata; the offline snapshot in `docs/action-pins.json` does not independently prove an object is a commit.
- Inspect every commit being published for credentials, personal data, and machine identifiers. Preserve unrelated contributors' work.
- Verify the private vulnerability reporting channel linked from SECURITY.md.
- Check repository/package metadata, documentation links, changelog, and the version/tag agreement.
- Wait for the exact commit's required CI jobs and inspect the independent coverage upload. Never substitute a static green badge for a failed or missing run.

## Release and metadata

Create a version tag and GitHub release from the verified commit and attach the wheel/source archive built from that same commit. Keep the Action example pinned to a published release, and recommend full commit SHA pins for immutable consumer dependencies.

Repository topics describe dotenv, environment variables, schema validation, CI, Python, and deployment. Package URLs point to the actual repository, documentation, issues, and changelog. The four README badges link to the GitHub release, Checks workflow, Codecov report, and MIT license.

A Marketplace listing is separate from distributing an Action from its repository. PyPI is also a separate destination: only advertise `uvx env-contract-check` after the package exists there and its installation has been checked. No package registry credentials are included in this repository.

Python-version classifiers and SPDX `license = "MIT"` plus `license-files` are used. Do not add deprecated `License ::` classifiers alongside modern SPDX licensing. Reference: [PyPA project metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license-and-license-files).
