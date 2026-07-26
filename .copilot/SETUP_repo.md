# Instructions — bring tabularium up to standard repo hygiene

**From**: Eric, 2026-07-09 — "instructions for github copilot to set up
the repo... standard content and other."

## What's missing

Compared to `eaprime1/custos` (the sibling repo, same owner, already has
this baseline), tabularium is missing standard repo files:

- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `LICENSE` (check what custos uses, if anything's been chosen)
- `CHANGELOG.md`
- `.codacy.yml` (if the codacy integration applies here too — check first,
  don't assume)

custos already has `.github/workflows/` CI (claude-code-review,
dependency-review, finalize-pr, track-pr-failures) — tabularium PR #3
already ported the same four workflows here, so that part's done. Verify
they still match if custos's have moved on since.

## How to do it

1. Pull the current versions of each file from `eaprime1/custos` (root of
   `main` branch) as the starting template.
2. Adapt content that's custos-specific (project name, description,
   contact info, any custos-only lore references) to fit tabularium's
   actual purpose — a personal library-cleanup pipeline, not the lore
   system. Don't just copy-paste verbatim if the content doesn't fit.
3. Open a PR, don't push directly to `main`.
4. Flag anything you're unsure whether to include (e.g. `.codacy.yml` —
   only add it if you can confirm the Codacy integration is meant to cover
   this repo too).

## Also flagged, not part of this task but worth knowing

The `claude-code-review` GitHub Action on this repo is currently failing
on every PR because the `CLAUDE_CODE_OAUTH_TOKEN` repo secret was never
set — Eric knows and is handling it separately. Not something to fix as
part of this setup task.
