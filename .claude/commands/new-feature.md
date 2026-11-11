---
description: Full workflow for a feature or bug (issue, branch, code, tests, PR)
argument-hint: <issue number, or a description if the issue does not exist yet>
---

Work on: $ARGUMENTS

Follow the "Workflow" section of `CLAUDE.md` and `.claude/rules/`:

1. If `$ARGUMENTS` is an issue number, read it with `gh issue view`. Otherwise create the issue
   first with `gh issue create` (check `gh issue list` for duplicates).
2. Branch `<n>-<type>-<slug>` from an up-to-date `main`.
3. Implement the simplest thing that works; reuse existing libraries and helpers.
4. Write the tests for this issue (or update the existing ones if no new test is needed); run `pytest` until green.
5. Commit as `type: summary (#n)` under the user's identity, with no Co-Authored-By or "Generated with" lines.
6. `git push -u origin <branch>` and `gh pr create` (body: what/why, `Closes #n`, how tested, no attribution line).
7. Stop and give the PR link. The user merges.
