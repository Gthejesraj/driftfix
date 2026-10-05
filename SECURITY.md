# Security Policy

## Reporting a vulnerability

Please **don't** open a public issue. Report it privately through
[GitHub security advisories](https://github.com/Gthejesraj/driftfix/security/advisories/new).
You'll get a response within a few days.

## Threat model: what to know before using driftfix

- **The agent can run commands.** driftfix gives Claude file editing and shell
  access inside the checkout so it can run your tests. Run it in CI or in a
  throwaway clone, never in a directory with secrets you don't want read.
- **Your code goes to the Anthropic API.** Relevant source files and test
  output are sent to Claude to produce the fix.
- **Dependency PRs come from outside.** A malicious package update could ship
  code that runs during your test suite. That's true of any CI that tests
  Dependabot PRs; driftfix doesn't add to it, but it doesn't protect you from
  it either.
- **Nothing is merged automatically.** driftfix pushes a commit to the PR, and
  a human reviews and merges it.
- **API key scope.** Store `ANTHROPIC_API_KEY` as a Dependabot secret, and set
  a spend limit on the key in the Anthropic console.

## Supported versions

Only the latest release gets fixes.
