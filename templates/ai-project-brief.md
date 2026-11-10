# AI Project Brief

Use this template when asking an AI assistant to help with a repository. Fill in only what is relevant. Do not include secrets or confidential information.

## Project

- Repository: [owner/repository and URL]
- Primary branch: [branch]
- Project purpose: [one or two sentences]
- Current state: [what is known to work]
- Important constraints: [license, platform, offline requirements, compatibility]

## Goal

[Describe one concrete outcome. Explain who benefits and how success will be checked.]

## Work boundaries

- Inspect the repository before proposing changes.
- Preserve existing behavior unless a change is explicitly required.
- Do not edit unrelated files.
- Do not invent test results, repository facts, users, or capabilities.
- Do not add paid services, telemetry, network dependencies, or dependencies without explaining the need and asking first.
- Do not expose secrets or private information.
- Do not publish, merge, delete, change permissions, or trigger external side effects without explicit approval.

## Required workflow

1. Inspect the current branch, working state, relevant files, tests, and recent history.
2. Summarize what already exists and identify gaps with file-level evidence.
3. Propose a small, ordered plan and identify risks.
4. Implement on a separate branch.
5. Add or update tests for changed behavior.
6. Run relevant checks and report exact commands and actual outcomes.
7. Inspect the final diff for unrelated changes, secrets, generated files, and regressions.
8. Open a pull request only when authorized.
9. Report what changed, what did not change, what remains unverified, and the next safe step.

## Evidence standard

For each important claim, distinguish:
- Observed in repository
- Tested locally or in CI
- Inferred
- Proposed
- Unknown / not tested

A passing test suite proves only the tested cases in the environment where it ran. Do not claim production readiness or security certification without independent evidence.

## Final report format

- Objective
- Files inspected
- Files changed
- Behavior changed (or explicitly unchanged)
- Tests run and results
- Risks and limitations
- Unresolved questions
- Branch / pull request link, if created
- Exact approval still needed, if any
