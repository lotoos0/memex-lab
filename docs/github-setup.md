# GitHub Setup

This repository should use a safe but lightweight GitHub workflow:
- protect `main`
- block direct pushes to `main`
- require pull requests for all changes
- keep PRs small and scoped
- use the minimum review and automation needed for early-stage work

## Audit summary

Repository state at the time of this setup:
- no existing `.github/` directory
- no existing pull request template
- no existing GitHub Actions workflow
- no repo-side automation for branch protection
- existing workflow guidance only in local docs such as `README.md`, `AGENTS.md`, `CLAUDE.md`, and `workflow.txt`

GitHub branch protection cannot be enforced from normal repository files alone. A human with repository admin access must apply the server-side settings in the GitHub UI.

## Intended workflow

Use this branch and PR model:
1. start from `main`
2. create one scoped branch for one task
3. make the smallest useful change
4. verify the change
5. open a pull request into `main`
6. review the PR
7. merge only after approval and any required checks pass

Recommended branch names:
- `task/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`

Keep the workflow lightweight:
- prefer one PR per scoped change
- avoid mixed refactors and feature work in the same PR
- do not silently expand scope
- prefer squash merge for a clean history

## Codex rules in this repo

Codex must use GitHub through branches and pull requests only:
- never push directly to `main`
- create a task branch for each scoped change
- open a PR for each completed change
- keep changes small and reviewable
- use PR review before merge
- do not expand scope silently

If a task grows beyond the original scope, stop and split it into a follow-up branch and PR instead of widening the current change.

## Manual GitHub UI settings

Apply these settings manually in GitHub with a repository admin account.

Recommended path:
1. open the repository on GitHub
2. go to `Settings`
3. open `Rules` or `Branches`
4. create protection for branch `main`

Use either a branch ruleset or a classic branch protection rule. The exact UI layout may differ, but the required settings should be:

### Required protection for `main`

- Branch name or target: `main`
- Require a pull request before merging: enabled
- Required approvals: `1`
- Dismiss stale approvals when new commits are pushed: enabled
- Require conversation resolution before merging: enabled
- Allow force pushes: disabled
- Allow deletions: disabled

### Direct-push blocking

To make direct pushes to `main` effectively blocked:
- do not grant bypass access for normal development
- if your GitHub UI shows `Do not allow bypassing the above settings`, enable it
- if your GitHub UI uses rulesets with a bypass list, keep the bypass list empty unless you intentionally want an emergency admin path

### Status checks

This repo now includes one minimal GitHub Actions check in `.github/workflows/python-syntax-check.yml`.

If the workflow runs reliably in GitHub, enable:
- Require status checks to pass before merging: enabled
- Required status check: `python-syntax-check`

If the check becomes flaky or stops matching the repository state, remove it from required checks until it is fixed. Do not require checks that are not dependable.

### Keep these off for now

Do not add these yet unless the workflow becomes more complex:
- CODEOWNERS review requirement
- merge queue
- signed commits requirement
- linear history requirement
- deployment requirements
- heavy CI/CD gates

## PR guidance

Each pull request should answer:
- what changed
- why it changed
- how it was verified
- what remains out of scope

PRs should stay small enough that review is fast and specific.

## Minimal status check

The repository includes a lightweight GitHub Actions workflow named `python-syntax-check`.

Purpose:
- catch basic Python syntax errors before merge
- keep branch protection simple
- avoid adding heavy CI before the project needs it

Current command:

```bash
python -m compileall collector
```

This is intentionally narrow because the current project stage is collector-first and the collector is the only implemented Python package in active use.
