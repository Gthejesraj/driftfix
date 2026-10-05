# Changelog

## 0.2.1
- Test commands no longer see `ANTHROPIC_API_KEY` or GitHub tokens
- Report the real cost when the agent stops on its budget (was $0.00)
- The pinning-back guard now allows widening the requirement to admit the new version (e.g. dropping `<2.0.0`)

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
