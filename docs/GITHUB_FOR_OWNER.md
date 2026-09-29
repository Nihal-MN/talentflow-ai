# GitHub for the Repository Owner — a zero-to-confident guide

You built a project; this page teaches you the platform it lives on. Nothing
here requires prior GitHub knowledge. Read it once with the repository open in
front of you.

---

## 1. The vocabulary, in plain words

| Term | What it actually means |
|---|---|
| **Repository (repo)** | The project folder on GitHub: files + the full history of every change. Yours: `github.com/Nihal-MN/talentflow-ai`. |
| **Clone** | Downloading a copy of the repo to a computer (`git clone <url>`). You have a clone locally. |
| **Commit** | A saved change with a message ("fix: handle empty uploads"). History is a chain of commits. |
| **Branch** | A parallel line of work. `main` is the default/real one; you make short-lived branches for changes (`feat/x`, `fix/y`). |
| **Pull Request (PR)** | "Please merge my branch into main." Shows exactly what changed, runs CI, invites review — even on your own work. The place where merging happens. |
| **Issue** | A tracked task/bug/question. Not a chat — a durable record. |
| **Merge** | Combining a branch into another (usually into `main`). |
| **Conflict** | Two changes touched the same lines; git asks a human to pick. Normal, not scary: edit the marked file, keep what's right, commit. |
| **Tag** | A sticky name pinned to one commit — releases use them (`v0.1.0`). |
| **Release** | A GitHub page for a tag: title + notes + downloadable source. What users of your project see as "a version". |
| **Fork** | Someone's own copy of your repo, on their account. They change it, then PR back. |
| **GitHub Actions** | GitHub's robots. On every push they run your workflows (`.github/workflows/*.yml`). |
| **CI** | "Continuous Integration" — the habit of letting robots test every change. Here: your CI workflow runs backend tests on real PostgreSQL, frontend tests + build, and Docker builds. |
| **Workflow / run** | One robot script (`ci.yml`, `codeql.yml`) and one execution of it (visible under the repo's **Actions** tab). |
| **Contributor** | Anyone whose code/docs/issue landed in the project. |
| **Maintainer** | Someone who decides what gets merged/released and keeps the project healthy. Right now: you. |
| **Star** | A bookmark/thanks from a visitor. Purely a signal — never buy, trade, or fake them. |
| **Watch** | "Notify me about this repo" — for people following your project. |

## 2. Your normal workflow (the loop)

```
Issue  →  branch  →  code  →  tests  →  PR  →  review  →  merge  →  release
```

Concretely, for a small fix:

```bash
# 0. sync up
git switch main && git pull

# 1. branch
git switch -c fix/upload-hint

# 2. code, then run the guards
make test && make lint

# 3. commit and push
git add -A && git commit -m "fix: clarify upload hint text"
git push -u origin fix/upload-hint

# 4. open the PR (browser also works: the repo shows a "Compare & pull request" button)
gh pr create --fill

# 5. watch CI on the PR page; when green, merge:
gh pr merge --squash --delete-branch

# 6. when enough has landed → release (docs/RELEASE_CHECKLIST.md):
git switch main && git pull
git tag -a v0.1.1 -m "v0.1.1" && git push origin v0.1.1
gh release create v0.1.1 --title "v0.1.1" --notes "…"
```

## 3. Things you can do entirely in the browser

- **Edit any file**: open the file → pencil icon → commit ("Commit changes").
  Good for README/typo fixes. For anything bigger, use a branch + PR.
- **Open a PR from a branch**: after pushing, the repo homepage shows a
  "Compare & pull request" button.
- **Review a PR**: the **Files changed** tab shows the diff; comment on any
  line; "Approve" or "Request changes".
- **Merge**: green "Merge pull request" button (choose "Squash and merge" to
  keep history tidy).
- **Create a release**: repo → right sidebar → **Releases** → "Draft a new
  release" → pick/create the tag → write notes → Publish.
- **Settings**: the **Settings** tab (gear). See §5.

## 4. The tabs you'll actually use

| Tab | What it's for |
|---|---|
| **Code** | Files + README (the front page of the project). |
| **Issues** | Tasks and bugs. Your first real contributions might start here. |
| **Pull requests** | Proposed changes + where CI results show. |
| **Actions** | Every CI run. Red X on a commit? Click it → the failing job → logs. |
| **Security** | Dependabot alerts, CodeQL results, private vulnerability reports. |
| **Insights** | Traffic/stars over time. Look occasionally; don't chase numbers. |

## 5. Settings worth knowing (one-time setup)

`Settings → General`: repository name, description, **topics**, social preview
image. `Settings → Branches`: branch protection rules (e.g. require CI before
merge into `main`). `Settings → Security`: private vulnerability reporting
toggle, Dependabot toggles. `Settings → Pages`: free static hosting for docs
sites (not used yet).

## 6. When something goes wrong

- **CI is red on main**: click the failing run under Actions → read the last
  lines of the failing step → fix locally → push again. Red main for hours
  is normal in real projects; the sin is leaving it red for days.
- **A bad change is merged**: `git revert <sha>` then push (see
  `docs/MAINTAINER_GUIDE.md §11`). Never rewrite `main`.
- **A PR conflicts**: GitHub shows "Resolve conflicts" (web editor) or locally:
  merge `main` into your branch, fix the marked files, commit.
- **You feel lost**: `git status` and `git log --oneline -10` answer "where am
  I?" 90% of the time.

## 7. Rules of the road (for you, too)

- Never force-push `main`. Never commit `.env` or API keys.
- Synthetic data only — in examples, tests, screenshots, issues.
- Small PRs beat big ones; one change per PR.
- Thank every reporter and contributor. That's the whole culture.
