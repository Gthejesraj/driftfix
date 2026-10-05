# driftfix

[![PyPI](https://img.shields.io/pypi/v/driftfix)](https://pypi.org/project/driftfix/)
[![CI](https://github.com/Gthejesraj/driftfix/actions/workflows/ci.yml/badge.svg)](https://github.com/Gthejesraj/driftfix/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/driftfix)](https://pypi.org/project/driftfix/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Dependabot bumps it. CI breaks. driftfix fixes the code.**

Dependency bots open the upgrade PR, then leave you to fix whatever broke.
driftfix finishes the job: it reads the failing tests, has Claude adapt your
code to the new version, reruns your tests itself, and pushes the fix onto the
same PR. If it can't get to green, it comments what it tried and commits
nothing.

```
Dependabot PR (openai 0.28 → 1.x)
  → tests fail
  → Claude reads the failure + changelog, edits your code
  → driftfix reruns your tests
      ✅ green → fix committed to the PR, with an explanation
      ❌ red   → comment only, nothing committed
```

See it on a real Dependabot PR: [driftfix-playground#1](https://github.com/Gthejesraj/driftfix-playground/pull/1).

## Benchmark

Real breaking upgrades. Each case is a small app whose tests pass on the old
version and fail on the new one. Most include a trap beyond renames: a silent
behavior change, a security footgun, or a multi-file refactor.

<!-- bench -->
| Package | Upgrade | Fixed | Cost | Diff |
|---|---|---|---|---|
| httpx | 0.27.2 → 0.28.1 | ✅ | $0.12 | 1 file changed, 4 insertions(+), 1 deletion(-) |
| numpy | 1.26.4 → 2.5.3 | ✅ | $0.14 | 1 file changed, 5 insertions(+), 5 deletions(-) |
| openai | 0.28.1 → 3.24.0 | ✅ | $0.29 | 1 file changed, 4 insertions(+), 3 deletions(-) |
| pydantic | 1.10.21 → 2.13.5 | ✅ | $0.20 | 1 file changed, 11 insertions(+), 11 deletions(-) |
| sqlalchemy | 1.4.54 → 2.1.3 | ✅ | $0.19 | 1 file changed, 7 insertions(+), 4 deletions(-) |
| pydantic (6-file app, shared base model) | 1.10.21 → 2.13.5 | ✅ | $0.51 | 4 files changed, 47 insertions(+), 29 deletions(-) |
| pydantic (`BaseSettings` moved to new package) | 1.10.21 → 2.13.5 | ✅ | $0.22 | 2 files changed, 8 insertions(+), 5 deletions(-) |
| pandas | 1.5.3 → 2.3.3 | ✅ | $0.19 | 1 file changed, 5 insertions(+), 5 deletions(-) |
| django | 3.2.25 → 5.2.17 | ✅ | $0.20 | 1 file changed, 7 insertions(+), 8 deletions(-) |
| flask | 2.2.5 → 3.1.3 | ✅ | $0.22 | 1 file changed, 6 insertions(+), 12 deletions(-) |
| pillow | 9.5.0 → 12.3.0 | ✅ | $0.13 | 1 file changed, 3 insertions(+), 2 deletions(-) |
| pyyaml | 5.4.1 → 6.0.3 | ✅ | $0.18 | 1 file changed, 2 insertions(+), 2 deletions(-) |

**12/12 fixed, $2.59 total** ($0.12–$0.51 per fix).
<!-- /bench -->

Every fix was verified by rerunning the tests, and no test was edited.
Reproduce with `python bench/run.py` (needs an API key), or validate the cases
for free with `python bench/run.py --check`.
**Found an upgrade it can't fix? That's the most useful contribution:** see
[CONTRIBUTING.md](CONTRIBUTING.md).

### Real projects

The synthetic cases above are small. On real open-source projects broken by
pydantic 1 → 2 ([study](https://github.com/Gthejesraj/driftfix-study), 39
candidates → 4 real breaks):

| Project | Tests broken | Result | Cost |
|---|---|---|---|
| internetarchive/fatcat-scholar | 15 of 115 | ✅ fixed, 11 files | $2.38 |
| antonagestam/phantom-types | 2 of 677 | ✅ fixed, one test assertion edit to review | $2.93 |
| epi2me-labs/ezcharts | 5 of 37 | ✅ fixed, including the model generator | ~$1 |
| bdd100k/bdd100k | 2 of 46 | ⚠️ tests pass, but via a workaround for a third-party library | $0.95 |

Real fixes cost $1–3, not $0.20, so set `budget` to at least 3 for real
codebases. Always read the diff: "tests pass" and "correct" aren't the same
thing. Details in the study's [RESULTS.md](https://github.com/Gthejesraj/driftfix-study/blob/main/RESULTS.md).

## Quick start: GitHub Action

1. Add `.github/workflows/driftfix.yml`:

   ```yaml
   name: driftfix
   on: pull_request
   permissions: { contents: write, pull-requests: write }
   jobs:
     fix:
       if: github.actor == 'dependabot[bot]'
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with: { ref: "${{ github.head_ref }}" }
         - uses: Gthejesraj/driftfix@v0
           with:
             anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
             setup: pip install -r requirements.txt   # however you install deps
             test: pytest -q                          # however you run tests
   ```

2. Add `ANTHROPIC_API_KEY` under **Settings → Secrets and variables →
   Dependabot**. Workflows triggered by Dependabot can't read your normal
   Actions secrets.

That's it. The next Dependabot PR that breaks your tests gets a fix commit.

| Input | Default | |
|---|---|---|
| `anthropic-api-key` | required | |
| `setup` | `pip install -r requirements.txt` | command that installs dependencies |
| `test` | `pytest -q` | any command; exit code 0 = green |
| `package` | from Dependabot | set it for non-Dependabot PRs |
| `model` | `claude-opus-5` | |
| `budget` | `5` | max USD per run |

## Quick start: CLI

```bash
pip install driftfix
export ANTHROPIC_API_KEY=sk-ant-...
# you upgraded a dependency and your tests fail:
driftfix fix --package openai --from 0.28 --to 1.40 --test "pytest -q"
```

Flags: `--test`, `--model`, `--budget` (USD, default 5), `--max-turns`
(default 50), `--timeout` (test timeout, seconds), `--summary FILE` (write the
markdown report), `--repo PATH`.

Exit codes: `0` fixed or nothing to fix, `1` not fixed, `2` dirty working tree.

## Guardrails

- **Your tests decide.** driftfix reruns them after the agent finishes. The
  agent saying it's done doesn't count.
- **No pinning back.** A requirement that excludes the new version, or any
  lock file edit, is rejected. Widening a requirement so the new version is
  allowed (dropping an old `<2` cap) is fine, and so is adding a package the
  upgrade split out (like `pydantic-settings`).
- **No deleting or skipping tests.** The agent is told not to, and every test
  change shows up in the diff you review.
- **Reviewable.** It needs a clean git tree, so every change is a diff, and it
  never merges.
- **Bounded.** Spend cap per run, and the cost is printed in every report.

See [SECURITY.md](SECURITY.md) for the threat model. The short version: the
agent can run commands inside the checkout, so run it in CI or a throwaway
clone.

## FAQ

**What does it cost?** $0.12–0.51 per fix in the benchmark, billed to your
Anthropic API key. When tests already pass, Claude isn't called at all.

**Does my code leave my machine?** Yes. The relevant files and test output
are sent to the Anthropic API.

**Which languages?** Python is what's benchmarked. The Action takes any
`setup` and `test` command, so npm projects should work, but that's untested.
Reports are welcome.

**Renovate instead of Dependabot?** Use the CLI or set the `package` input.
Native Renovate support is on the roadmap.

**Why doesn't CI rerun after the fix commit?** GitHub doesn't trigger
workflows from commits pushed with the default `GITHUB_TOKEN`. Pass a personal
access token or GitHub App token to `actions/checkout` if you want that.

**Can it fix deprecations before they break?** Yes. Make the test command
treat them as errors, e.g. `pytest -q -W error::DeprecationWarning` (some
libraries use their own warning class, like
`-W error::starlette.exceptions.StarletteDeprecationWarning`). On a real
31-file FastAPI app, this caught Starlette's `httpx` → `httpx2` deprecation and
fixed it with a one-line dependency swap ($0.40).

**Mocked tests?** driftfix can only catch what your tests catch. A test that
mocks the library can pass while the real call is broken.

## Roadmap

- More benchmark cases (langchain, Django REST framework), larger real repos
- npm and Renovate support
- Provider mode: packages publish migration notes that driftfix reads

## Contributing

Bug reports, failed-fix reports and benchmark cases are all welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
