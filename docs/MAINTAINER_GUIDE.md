# Maintainer Guide — TalentFlow AI

For the project owner, as a first-time open-source maintainer. Short rules,
exact commands. Nothing here assumes prior GitHub experience — for the raw
vocabulary, read `GITHUB_FOR_OWNER.md` first.

---

## The job in one paragraph

A maintainer's loop is: **triage what came in → keep `main` green → ship
releases → say thank you.** Everything below is a detail of that loop. You
never have to do any of it fast; you only have to be clear and kind.

## 1. Reviewing issues

- New issue arrives → read it → apply a label (`gh issue edit 12 --add-label bug`)
  and, if it's small and clear, `good first issue`.
- If it's a bug you can't reproduce, ask for the missing bit from the template
  (environment / exact steps) — one question, not an interrogation.
- If it's a real bug: leave a short "confirmed, here's what I think is
  happening" comment. That single sentence is worth a lot to reporters.
- Close duplicates with a link to the canonical issue. Close "won't fix" with
  one honest sentence of why (scope, non-goal per ROADMAP, etc.).
- Never leave an issue unanswered for more than a week if you can help it.
  A slow answer is fine. Silence is not.

## 2. Creating branches (for your own work)

```bash
git switch main && git pull
git switch -c feat/candidate-filters        # or fix/, docs/, chore/
# work, commit (conventional style: feat:, fix:, docs:, test:, chore:)
git push -u origin feat/candidate-filters
gh pr create --fill     # open the PR for CI + history
```

Even solo, work through PRs for anything non-trivial: it gives you CI, a
reviewable diff, and a clean revert point.

## 3. Accepting a community PR

1. Read the PR description → the diff. Run the checklist in your head:
   synthetic data only? explainability kept? tests included?
2. Pull it locally and run the suite — never merge on faith:

```bash
gh pr checkout 34
make test && make lint
```

3. If it's good: approve on GitHub (Files changed → Review changes → Approve),
   then merge. Prefer **Squash and merge** for tidy history (button on the PR),
   or `gh pr merge 34 --squash --delete-branch`.
4. If it's almost good: request changes with *specific* asks ("please add a
   regression test for X; rename Y for consistency"). Thank them.

## 4. Rejecting a PR (politely)

You're allowed to say no. The template: thank them → state the reason in one
sentence (out of scope / conflicts with RESPONSIBLE_AI contract / too large to
review) → point at ROADMAP or the relevant doc → close the PR. Never just
close silently.

## 5. Merging safely

- `main` is protected by convention: **CI must be green before merge**.
- If CI is red on their branch and green reasons are unclear, ask them to fix;
  don't "fix it for them" by pushing to their fork.
- Big PR? It's fine to ask the contributor to split it.
- After merge: delete the branch (`--delete-branch` above does it).

## 6. When to release

Release when you have a meaningful set of changes and CI is green — there is
no schedule pressure. Run `docs/RELEASE_CHECKLIST.md` top to bottom. For a
solo project, one release per batch of merged work is right; don't tag every
small fix.

## 7. Versioning

Semantic Versioning: **fix → patch** (0.1.1), **feature → minor** (0.2.0),
**breaking → major** (1.0.0). Stay in `0.x` while the API can still change.
Update `CHANGELOG.md` (move `Unreleased` items into the new version with
today's date) before tagging.

## 8. Updating the changelog

Keep a Changelog sections: Added / Changed / Fixed / Security. Write for a
user of the software, not for a git log reader: "Candidates page no longer
drops files after the first" beats "fix FileList bug". One line per change.

## 9. Handling security reports

- If someone opens a public issue containing a vulnerability: respond kindly
  ("thanks — please move this to a private advisory") and, if needed, hide
  the content. Then continue in private.
- Private advisories (Security tab → Advisories) are the right place: discuss,
  fix on a private branch, and when fixed use "Request CVE" only if genuinely
  warranted for a demo-scale project.
- Fix, release a patch version, then publish the advisory with credit if the
  reporter wants it.

## 10. Dependency PRs (Dependabot)

- Grouped minor/patch PRs: click CI green → merge (Squash). Read the CI diff
  if anything failed.
- Major version bumps: read the release notes of the dependency first; they
  often need a small migration. If it fails, close it and open an issue
  "Upgrade X to vN" so it's not lost.
- Never merge a dependency PR with red CI "to see what happens".

## 11. Reverting a bad change

If a bad change is already on `main`:

```bash
git switch main && git pull
git revert <bad-commit-sha>        # creates a "Revert ..." commit
git push
```

Revert, don't rewrite: `git revert` keeps history honest and works with
branch protection. If the revert conflicts (later work built on it), revert
the smallest coherent commit or ask the original author for help.

## 12. Burning out is a bug

You owe no one a merge. Slow is allowed; rude is not; "not now" is a complete
response. Triage to zero weekly, answer what you can, and let the rest wait.
