# Changelog

## Unreleased
- Test commands no longer see `ANTHROPIC_API_KEY` or GitHub tokens

## 0.2.0
- 5 more benchmark cases: pandas 2, Django 5, Flask 3, Pillow 10, PyYAML 6
- `driftfix --version`
- Contributor guide, security policy, issue templates, CI on Python 3.10–3.13

## 0.1.1
- May add a package the upgrade split out (e.g. `pydantic-settings`).
  Changing the upgraded package's requirement or editing lock files is still
  rejected.

## 0.1.0
- First release: `driftfix fix` CLI and GitHub Action
- Benchmark: openai, pydantic, SQLAlchemy, numpy, httpx
