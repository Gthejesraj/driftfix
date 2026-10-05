# Contributing to driftfix

Thanks for helping. driftfix is small on purpose: one CLI module, one GitHub
Action, and a benchmark. Contributions that keep it that way are the easiest to
merge.

## Setup

```bash
git clone https://github.com/Gthejesraj/driftfix && cd driftfix
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
pytest -q && ruff check .
```

The unit tests replace Claude with a fake agent, so they're free and need no
API key.

## The most useful contribution: a benchmark case

Every case is a breaking upgrade that driftfix should be able to fix. Cases it
*fails* on are just as valuable as cases it passes. They show us what to
improve.

1. Create `bench/cases/<name>/` with:
   - `app.py` (or a package) written against the **old** version
   - `tests/` that exercise the behavior, **not** mocks of the library (a mock
     can hide the breakage; see `bench/cases/openai` for a fake-server
     pattern)
   - `pytest.ini` with `pythonpath = .`
   - `case.json`:
     ```json
     {"package": "pandas", "old": "pandas==1.5.3 numpy<2", "new": "pandas>=2,<3", "python": "3.11"}
     ```
     `old`/`new` are space-separated pip specs; `python` defaults to 3.12.
   - optional `build-constraints.txt` if the old version needs build pins
2. Check it's a real break (free, no API calls):
   ```bash
   python bench/run.py --check <name>   # must print "old pass  new fail  ok"
   ```
3. Optionally run driftfix on it (needs `ANTHROPIC_API_KEY`, about $0.10–0.50):
   ```bash
   python bench/run.py <name>
   ```
4. Open a PR. Include the result if you ran it.

Good cases have at least one **trap** beyond renames: a silent behavior change,
a security footgun, or a fix that has to touch several files.

## Code changes

- Open an issue first for anything bigger than a bug fix.
- Keep the guardrails intact: tests decide success, no pinning back, no
  skipped tests, no silent publishing.
- Add a test in `tests/` for any behavior change.
- `pytest -q` and `ruff check .` must pass.

## Reporting a failed fix

If driftfix couldn't fix a real upgrade, open a
[failed fix issue](https://github.com/Gthejesraj/driftfix/issues/new?template=failed_fix.yml).
Those reports become benchmark cases. Please strip secrets and private code
first.
