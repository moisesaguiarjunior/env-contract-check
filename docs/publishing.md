# Publication checklist — not executed

Publication remains outside the current authorization. This is prepared metadata, not a claim that public endpoints or releases exist.

## Local readiness

- Reconcile the independent review findings against the corrected commit.
- Run the documented checks, package-install smoke, and `uv run --locked python tools/verify_action_pins.py` (explicitly online, public metadata only). The offline pin regression uses `docs/action-pins.json`; it does not replace live object-type verification when pins change.
- Confirm the founder's intended public Git author identity before exposing history. Do not rewrite the existing local history automatically.
- Configure a real private vulnerability-reporting channel before replacing the local-only SECURITY.md instructions.

## Public metadata to activate after authorization

Suggested repository description:

> Validate .env files against a typed schema, detect .env.example drift, and block misconfigured deployments. Python CLI + GitHub Action.

Suggested topics: `dotenv`, `environment-variables`, `configuration-validation`, `schema-validation`, `github-actions`, `deployment`, `python`, `cli`, `devtools`.

Once the repository exists, add verified destinations to `pyproject.toml`:

```toml
[project.urls]
Repository = "https://github.com/moisesaguiarjunior/env-contract-check"
Documentation = "https://github.com/moisesaguiarjunior/env-contract-check#readme"
Issues = "https://github.com/moisesaguiarjunior/env-contract-check/issues"
Changelog = "https://github.com/moisesaguiarjunior/env-contract-check/blob/main/CHANGELOG.md"
```

These destinations are reserved proposals; they are intentionally not live package metadata yet. Python-version classifiers and SPDX `license = "MIT"` plus `license-files` are already present. Do not add deprecated `License ::` classifiers alongside modern SPDX licensing. Reference: [PyPA project metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#license-and-license-files), consulted 2026-11-13.

After authorization, verify name availability and destination URLs, run hosted CI/Action tests, publish the reviewed package and `v0.1.0` release, then prepare the Marketplace listing. Replace the README SHA placeholder with the reviewed public commit, add real status/version badges, and switch installation examples to `uvx env-contract-check` only after the package actually exists on the index. Convert llms.txt links to the established canonical URLs at that point.

The README terminology/FAQ changes are discoverability hypotheses, not measured ranking improvements. `llms.txt` is a navigation aid. No SchemaStore submission, pre-commit hook, release, remote repository, Marketplace listing, or scheduled automation was created.
