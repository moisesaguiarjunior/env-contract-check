# Independent Sol follow-up review

Reviewed on 2026-11-13. Corrected commit: `0a005910b747c3e5abc2f426d8d4cb1c068b23da`. Comparison base: `4b78974e8635c1997495d0c8bd384fb0cb98b979`.

The three reported defects are closed for the behavior independently checked below. No new actionable defect was confirmed in this follow-up scope. This is local verification plus authorized read-only public GitHub metadata verification; it is not a hosted CI result, visual approval, publication approval, or proof that no bugs remain.

## Scope and independence

Reviewed the complete diff from the base, the current CLI/parser/validator, new pin verifier and pin snapshot, regression tests, Action and both workflow files, README, renamed `docs/reuse.md` and its references, changelog, publishing checklist, protocol/contract updates and source manifest. Rechecked the implementation boundaries established in the first review. Author validation notes were not accepted as evidence of reviewer execution.

No implementation, tests, configuration or existing documentation was modified. This follow-up report is the only repository file added by the reviewer. No agents were launched, remotes created, packages published, deployments attempted, or project files sent to an external service. The explicitly authorized public API requests contained only public Action repository names and object hashes.

## Disposition of prior findings

| Finding | Disposition | Independent evidence |
| --- | --- | --- |
| First Sol P3: buffered broken-pipe shutdown | Closed | Real closed OS-pipe subprocesses now exit 2 with empty stderr for text and JSON. The original source exits 120 with a shutdown exception under the same harness. |
| Opus EC-1: setup-uv annotated-tag hash | Closed for pin identity | Both active references now use commit `37802adc94f370d6bfd71619e3f0bf239e1f3b78`. GitHub Git commit endpoints independently accepted all three remote Action pins. The old hash resolves through the Git tag endpoint to that commit and is rejected by the new verifier through the Git commit endpoint. Hosted Action execution remains unverified. |
| Opus EC-2: leading hash silently becomes empty | Closed | `TOKEN=#synthetic` and `TOKEN= #synthetic` retain `#synthetic`. A contract allowing only an empty string now rejects that file with exit 1; the original source incorrectly accepts it with exit 0. Normal embedded hashes and trailing whitespace-separated comments retain their intended behavior. |

### Broken pipe

`src/env_contract_check/cli.py:122` now flushes inside the protected output operation and redirects the output file descriptor to the null sink after a broken pipe, preventing a second failure during interpreter shutdown. `tests/test_cli.py:211` exercises an actual subprocess and OS pipe rather than only replacing `print`.

The reviewer independently exported original and corrected Python sources into separate temporary package trees. Imports were checked to originate from the intended tree before each experiment. Identical valid synthetic inputs produced:

```text
                         Original             Corrected
closed pipe, text        exit 120; stderr      exit 2; empty stderr
closed pipe, JSON        exit 120; stderr      exit 2; empty stderr
```

The complete current test suite also ran successfully across Python 3.11–3.14, including these regressions.

### Action pins and verifier

`action.yml:34` and `.github/workflows/ci.yml:34` use the corrected setup-uv commit. `tools/verify_action_pins.py` discovers remote references in the root Action and active workflow YAML, requires full commit hashes, and verifies the Git commit object shape and exact returned hash. The offline snapshot test checks consistency with `docs/action-pins.json`; it does not independently prove the remote object type. That distinction is correctly documented in the publishing checklist.

Reviewer-executed live verification accepted:

- `actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803` — [Git commit metadata](https://api.github.com/repos/actions/checkout/git/commits/d23441a48e516b6c34aea4fa41551a30e30af803).
- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` — [Git commit metadata](https://api.github.com/repos/actions/setup-python/git/commits/ece7cb06caefa5fff74198d8649806c4678c61a1).
- `astral-sh/setup-uv@37802adc94f370d6bfd71619e3f0bf239e1f3b78` — [Git commit metadata](https://api.github.com/repos/astral-sh/setup-uv/git/commits/37802adc94f370d6bfd71619e3f0bf239e1f3b78).

The [old setup-uv object](https://api.github.com/repos/astral-sh/setup-uv/git/tags/94527f2e458b27549849d47d273a16bec83a01e9) returned tag `v7`, object type `commit`, and target hash `37802adc94f370d6bfd71619e3f0bf239e1f3b78`. This confirms the old reference was an annotated-tag object. A separate temporary verifier fixture using the old hash failed with HTTP 404 at the Git commit endpoint; a fixture using `@v7` was rejected locally before a request.

These requests establish object identity on the review date. They do not establish that upstream Actions, setup, or deployment run successfully on GitHub-hosted runners.

### Leading hashes

The removal in `src/env_contract_check/dotenv.py:27` eliminates the silent conversion of a leading hash into an empty string. Independent original/current source probes returned:

```text
Assignment               Original       Corrected
TOKEN=#synthetic         empty          #synthetic
TOKEN= #synthetic        empty          #synthetic
TOKEN=a#b                a#b            a#b
TOKEN=a #comment         a              a
```

The additional end-to-end empty-choice contract probe distinguishes a real gating correction from a parser-only assertion: original exit 0/valid became corrected exit 1/invalid. The synthetic value did not appear in either report. Current tests also cover accepting a contract choice containing the leading hash, with `allow_empty` both enabled and disabled. The contract reference documents the chosen dialect, including spaces immediately after `=` and the compatibility warning.

## Documentation and packaging

The README's new synthetic input block matches `examples/invalid.env`; the displayed three-issue report exactly matches independently executed CLI output. The shorter Action example preserves the gate inputs and links to the complete tag-triggered workflow. FAQs describe explicit file validation, example drift, failure propagation and the diagnostic boundary without claiming secret redaction for other logs.

All recursively discovered local Markdown links resolved, including the renamed reuse map references. The reuse map retains the existing canonical parser/validator/renderer owners and adds the pin-verification helper; no duplicate validator was introduced. The changelog identifies an unreleased candidate and the three corrections. The publishing checklist prepares future work without claiming public endpoints, measured discoverability, hosted CI or actual publication.

The newly built wheel contains byte-identical corrected CLI, dotenv and validation modules. Its metadata contains `License-Expression: MIT`, `License-File: LICENSE`, Python 3.11–3.14 classifiers, and no runtime dependency declarations. Source/wheel builds, Twine checks and a fresh isolated installed-wheel smoke test succeeded.

## Reviewer-executed checks

Except for the explicitly authorized GitHub public metadata requests, verification ran with `UV_OFFLINE=true` using locally available tools, dependencies and Python runtimes.

| Command/check | Result |
| --- | --- |
| `uv run --locked ruff check .` | Passed |
| `uv run --locked ruff format --check .` | Passed; 29 files checked |
| `uv run --locked mypy` | Passed; 15 source files checked |
| `uv run --locked pytest --cov --cov-report=term-missing` | 139 passed on Python 3.13; 98.24% branch-inclusive coverage |
| `uv run --locked --isolated --python 3.11 pytest -q` | 139 passed |
| `uv run --locked --isolated --python 3.12 pytest -q` | 139 passed |
| `uv run --locked --isolated --python 3.14 pytest -q` | 139 passed |
| `shasum -a 256 -c docs/source-manifest.sha256` | Every listed file matched |
| `uv build --no-sources` | Passed; wheel built from source distribution |
| `uv run --locked twine check dist/*` | Both distributions passed |
| `uv run --locked python tools/smoke_wheel.py` | Passed outside the checkout; temporary virtual environment removed |
| `uv run --locked python tools/verify_action_pins.py` | All three public commit objects verified live |
| Additional independent probes | Original/current source isolation; real closed pipes; leading-hash gating; verifier rejection of tag reference/tag object; exact README input/output; recursive local links; wheel source/metadata inspection |

The executed suite includes the existing actual-Bash Action adapter checks for literal arguments, invalid/missing generated files, example drift, strict mode and deployment blocking. Those tests continue to pass. Coverage does not instrument the subprocess launcher or the broken-pipe subprocess branch; actual process assertions, not coverage percentage, support the finding closure.

## Remaining limits

- No hosted CI/Action run, Windows execution, upstream setup-Action execution, fresh online toolchain bootstrap, cloud authentication or real deployment was tested. No actionlint execution was performed.
- README prose/examples and documentation structure were checked; no browser-rendered visual approval, public search result measurement or external agent discoverability measurement was performed. Alternative-tool descriptions were not independently researched in this follow-up.
- No broad new audit of unchanged parsers, exhaustive fuzzing campaign, dependency vulnerability audit or comprehensive resource-exhaustion analysis was performed. The first review's documented security and library boundaries still apply.
- The pin snapshot is historical evidence and must be reverified when pins change. The verifier currently targets the root Action and active workflow files; the consumer template intentionally retains its reviewed-commit placeholder.
- Temporary source trees, fixture files and the isolated wheel-smoke environment were removed. Invoked command sessions completed. Existing user work was preserved.

This conclusion applies to `0a005910b747c3e5abc2f426d8d4cb1c068b23da` and the scope above. No remaining defect from the three specified findings was reproduced; absence of new findings is not proof of absence of bugs. Publication and hosted validation remain separate work.
