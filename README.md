# driftfix

**Dependabot bumps it. CI breaks. driftfix fixes the code.**

Dependency bots open the upgrade PR, then leave you to fix whatever broke.
driftfix finishes the job: it reads the failing tests, has Claude adapt your
code to the new version, reruns your tests itself, and pushes the fix onto
the same PR. If it can't get to green, it comments what it tried and commits
nothing.

```
Dependabot PR (openai 0.28 → 1.x) → tests fail → Claude fixes code → tests rerun → ✅ commit on the PR
                                                                              └→ ❌ comment only
```

## Benchmark

Real breaking upgrades, each a small app with tests that pass on the old version and fail on the new one ([`bench/`](bench/)):

| Package | Upgrade | Fixed | Cost | Diff |
|---|---|---|---|---|
| httpx | 0.27.2 → 0.28.1 | ✅ | $0.12 | 1 file changed, 4 insertions(+), 1 deletion(-) |
| numpy | 1.26.4 → 2.5.3 | ✅ | $0.14 | 1 file changed, 5 insertions(+), 5 deletions(-) |
| openai | 0.28.1 → 3.24.0 | ✅ | $0.29 | 1 file changed, 4 insertions(+), 3 deletions(-) |
| pydantic | 1.10.21 → 2.13.5 | ✅ | $0.20 | 1 file changed, 11 insertions(+), 11 deletions(-) |
| sqlalchemy | 1.4.54 → 2.1.3 | ✅ | $0.19 | 1 file changed, 7 insertions(+), 4 deletions(-) |

5/5 fixed for $0.94 total, no test edits. Rerun: `python bench/run.py` (or `--check` to validate cases for free).
More cases welcome: add a folder under `bench/cases/`.

## GitHub Action

```yaml
# .github/workflows/driftfix.yml
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
      - uses: Gthejesraj/driftfix@main
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          setup: pip install -r requirements.txt
          test: pytest -q
```

**Important:** workflows triggered by Dependabot can't read your normal repo
secrets. Add `ANTHROPIC_API_KEY` under **Settings → Secrets → Dependabot**.

Commits pushed with the default `GITHUB_TOKEN` don't re-trigger CI. Use a PAT
or GitHub App token in `actions/checkout` if you want CI to rerun on the fix.

## CLI

```bash
pip install git+https://github.com/Gthejesraj/driftfix
# after upgrading a dependency and seeing tests fail:
driftfix fix --package openai --from 0.28 --to 1.40 --test "pytest -q"
```

| Flag | Default | |
|---|---|---|
| `--test` | `pytest -q` | any command; exit 0 = green |
| `--model` | `claude-opus-5` | |
| `--budget` | `5` | max USD per run |
| `--max-turns` | `50` | |
| `--summary FILE` | | write the markdown report |

## Guardrails

- Your tests decide. driftfix reruns them after the agent finishes; the agent's word doesn't count.
- Edits to dependency files (pinning back) are rejected.
- Requires a clean git tree, so every change is a reviewable diff.
- Never merges anything. The PR is still yours to review.
- The agent runs with full tool access inside the checkout. Run it in CI or a throwaway clone.

## Roadmap

- More benchmark cases (pandas 2, Django, langchain), harder multi-file repos
- npm / Renovate support
- Provider mode: packages ship migration notes that driftfix reads

## License

MIT
