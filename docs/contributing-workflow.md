# Contributing Workflow Reference

> **Audience:** all contributors — engineers, reviewers, and release managers.
>
> This document is the canonical quick-reference for the three enforcement gates that
> protect the `main` branch: **branch naming**, **PR review requirements**, and
> **lint / test requirements**. Each section links back to the full rationale in
> [`CONTRIBUTING.md`](../CONTRIBUTING.md) and the relevant ADR or DSN where applicable.
>
> Every rule here is also enforced mechanically: GitHub branch-protection rules enforce
> the CI status gates; Husky + lint-staged run pre-commit checks locally; the PR template
> includes a checklist that must be fully checked before requesting review.

---

## Table of Contents

1. [Branch Naming](#1-branch-naming)
   - [1a. Prefix table](#1a-prefix-table)
   - [1b. Naming rules](#1b-naming-rules)
   - [1c. Branch lifecycle](#1c-branch-lifecycle)
2. [Lint and Test Requirements](#2-lint-and-test-requirements)
   - [2a. Automated gates (CI)](#2a-automated-gates-ci)
   - [2b. Pre-commit hooks (local)](#2b-pre-commit-hooks-local)
   - [2c. Test coverage expectations](#2c-test-coverage-expectations)
   - [2d. Commands cheat-sheet](#2d-commands-cheat-sheet)
3. [PR Review Requirements](#3-pr-review-requirements)
   - [3a. Approval matrix](#3a-approval-matrix)
   - [3b. CI must be green before review](#3b-ci-must-be-green-before-review)
   - [3c. Review etiquette](#3c-review-etiquette)
   - [3d. Merge strategy](#3d-merge-strategy)
4. [End-to-End Gate Summary](#4-end-to-end-gate-summary)
5. [Common Failure Modes and Remediation](#5-common-failure-modes-and-remediation)

---

## 1. Branch Naming

> Full details: [`CONTRIBUTING.md §2`](../CONTRIBUTING.md#2-branching-strategy)

### 1a. Prefix table

| Prefix | Use for | Example |
|--------|---------|---------|
| `feat/` | New features or enhancements | `feat/PROJ-42-dark-mode` |
| `fix/` | Bug fixes | `fix/PROJ-99-login-redirect-loop` |
| `chore/` | Tooling, deps, CI config | `chore/upgrade-prisma-5` |
| `docs/` | Documentation-only changes | `docs/update-getting-started` |
| `refactor/` | Restructuring without behaviour change | `refactor/extract-auth-hook` |
| `test/` | Adding or fixing tests only | `test/add-upload-e2e` |
| `infra/` | Infrastructure-as-Code changes | `infra/add-cloudwatch-alarm` |
| `hotfix/` | Urgent fix branched from a release tag | `hotfix/v1.2.4-session-expiry` |

### 1b. Naming rules

| Rule | Detail |
|------|--------|
| Case | All **lowercase**; hyphens as word separators — no spaces, underscores, or extra slashes |
| Ticket number | Include where applicable: `feat/PROJ-123-short-description` |
| Maximum length | **60 characters** (enforced by the `check-branch-name` Git hook) |
| Single prefix | Each branch carries exactly one prefix from the table above |

**Valid examples:**

```
feat/PROJ-200-file-upload-ui
fix/mobile-nav-overflow
chore/upgrade-next-14-2
docs/adr-011-caching-strategy
refactor/extract-tenant-filter-hook
test/PROJ-301-cross-tenant-access
infra/ecs-autoscale-policy
hotfix/v2.0.1-presigned-url-expiry
```

**Invalid examples:**

```
Feature/darkMode          ❌  uppercase, no ticket, underscore
feat_dark_mode            ❌  underscores, no prefix separator
fix/PROJ-99/login-loop    ❌  extra slash inside the description
my-changes                ❌  no prefix
feat/this-branch-name-is-way-too-long-for-our-policy  ❌  > 60 chars
```

### 1c. Branch lifecycle

```
main ──────────────────────────────────────────► (always deployable)
      │                              ▲
      │  git checkout -b             │  squash-merge PR → delete branch
      ▼                              │
 feat/your-feature  ────────────────►
 (target ≤ 3 days; rebase on main before opening PR)
```

**Key lifecycle rules:**

1. **Always branch from `main`** — never from another feature branch.
2. **Rebase, never merge** — keep history linear; run `git rebase origin/main` before
   opening a PR.
3. **Delete after merge** — GitHub auto-deletes head branches on merge (branch-protection
   setting). Do not re-use a merged branch; create a new one.
4. **Force-push is allowed only on your own unshared branch** before the first push.
   Never `--force` a branch that a teammate has already pulled.

---

## 2. Lint and Test Requirements

> Full details: [`CONTRIBUTING.md §4f`](../CONTRIBUTING.md#4f-testing) and
> [`CONTRIBUTING.md §5a`](../CONTRIBUTING.md#5a-before-you-open-a-pr)

### 2a. Automated gates (CI)

The GitHub Actions CI pipeline runs on every push to a PR branch and on every push to
`main`. **All gates must be green before a PR can be merged** (branch-protection required
status checks).

| Gate | Command (per workspace) | Fails on | Workspace(s) |
|------|------------------------|----------|-------------|
| **Lint** | `npm run lint` | Any ESLint error or warning | `frontend/`, `backend/` |
| **Type-check** | `npm run type-check` | Any TypeScript error (`tsc --noEmit`) | `frontend/`, `backend/` |
| **Unit / integration tests** | `npm test -- --run` | Any failing test | `frontend/`, `backend/` |
| **Production build** | `npm run build` | Non-zero exit code | `frontend/`, `backend/` |
| **E2E tests** | `npm run test:e2e` | Any failing Playwright spec | `frontend/` (requires both services running) |
| **Generated types freshness** | `npm run generate:types && git diff --exit-code` | Stale `api-types.gen.ts` | `frontend/` |

> **Infrastructure changes:** PRs that modify `infra/` must additionally pass
> `npx cdk synth` (CloudFormation synthesis with no errors) as a required CI gate.

### 2b. Pre-commit hooks (local)

Husky + lint-staged run a subset of the CI checks **on staged files only** before every
`git commit`. This catches the most common issues within seconds — before pushing.

| Hook | Triggered by | Checks run |
|------|-------------|-----------|
| `pre-commit` | `git commit` | `eslint --fix-dry-run` + `tsc --noEmit` on staged `.ts` / `.tsx` files |
| `commit-msg` | `git commit` | Conventional Commits format check on the message header |

To bypass in a documented emergency (must be noted in the PR description):

```bash
git commit --no-verify -m "chore: emergency bypass — reason: ..."
```

### 2c. Test coverage expectations

New code must meet the following minimum coverage expectations. Failure to include tests
is a review blocker (see §3a).

| Code area | Required tests | Test type |
|-----------|---------------|-----------|
| New backend **service-layer** function | Happy path + ≥ 2 error paths | Unit (Vitest) |
| New **API route** (Express) | Auth failure + validation failure + success response | Integration (Supertest) |
| New **UI component** | Render + user interaction + accessible name/role | Component (React Testing Library) |
| New **critical user journey** | Full happy-path flow | E2E (Playwright) |
| Cross-tenant access on any new route | Request as Tenant A for Tenant B resource → `404` | Integration (Supertest) |

**Guiding principle:** test behaviour, not implementation. Assert what a user or API
consumer observes — not internal state, private methods, or module internals.

### 2d. Commands cheat-sheet

Run these locally before opening a PR. They mirror what CI runs exactly.

```bash
# ── Frontend ────────────────────────────────────────────────
cd frontend

npm run lint              # ESLint — must exit 0 with zero warnings
npm run type-check        # tsc --noEmit — must exit 0
npm test -- --run         # Jest — all tests, single run
npm run build             # next build — production build
npm run test:e2e          # Playwright — requires both services running on :3000/:4000
npm run generate:types    # regenerate api-types.gen.ts from backend OpenAPI spec

# ── Backend ─────────────────────────────────────────────────
cd backend

npm run lint              # ESLint — must exit 0
npm run type-check        # tsc --noEmit — must exit 0
npm test -- --run         # Vitest — all tests, single run (requires postgres container)
npm run build             # tsc → dist/ — must exit 0

# ── Both workspaces in one shot ─────────────────────────────
(cd frontend && npm run lint && npm run type-check && npm test -- --run && npm run build) && \
(cd backend  && npm run lint && npm run type-check && npm test -- --run && npm run build)
```

---

## 3. PR Review Requirements

> Full details: [`CONTRIBUTING.md §5`](../CONTRIBUTING.md#5-pull-request-process)

### 3a. Approval matrix

| PR type | Minimum approvals required | Who must approve |
|---------|---------------------------|-----------------|
| **Standard** — `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/` | **1** | Any other team member |
| **Infrastructure** — `infra/` prefix or changes under `infra/` | **2** | At least **1 infrastructure owner** |
| **Security-sensitive** — changes to auth, session, IAM, secrets, cookie config, tenant-isolation logic | **2** | At least **1 security owner** |
| **Breaking change** — commit footer contains `BREAKING CHANGE:` | **2** | At least **1 engineering lead** |

**How to identify security-sensitive PRs:**

A PR is security-sensitive if it touches any of the following:
- `backend/src/middleware/auth*`, session management, or cookie configuration
- `backend/src/routes/auth*` or any route that calls `requireSession`
- `middleware.ts` in the frontend
- AWS IAM roles, Secrets Manager configuration, or CDK security-group / SG rules
- The tenant-filter ESLint rule or any `// eslint-disable` on a Prisma query
- `SESSION_SECRET`, `DATABASE_URL`, or any secret-related environment variable handling

When in doubt, add the security owner as a reviewer.

**How to identify breaking changes:**

A commit is breaking if it:
- Removes or renames a public API endpoint path or method
- Changes a request or response body shape in a non-additive way
- Renames or removes a required environment variable
- Drops a database column that is still read by the previous application version

Mark breaking changes with the `BREAKING CHANGE` footer in the squash commit message and
include migration steps.

### 3b. CI must be green before review

Reviewers are **not required** to review a PR with a failing CI pipeline. The PR author
must fix all failures before requesting or re-requesting review.

Required status checks (enforced by GitHub branch protection):

```
✅ lint / frontend
✅ lint / backend
✅ type-check / frontend
✅ type-check / backend
✅ test / frontend
✅ test / backend
✅ build / frontend
✅ build / backend
✅ types-freshness / frontend    (on PRs that modify backend API contracts)
✅ cdk-synth / infra             (on PRs that modify infra/)
```

### 3c. Review etiquette

| Rule | Detail |
|------|--------|
| **Response time** | Reviewers respond within **1 business day**. If unavailable, reassign or comment with an expected timeline. |
| **Comment labelling** | Prefix blocking comments with `MUST:` and non-blocking suggestions with `nit:` or `suggestion:`. The author may address non-blocking comments at their discretion. |
| **Approval standard** | Approve only when you are satisfied the PR is correct, tested, and **safe to merge into production**. "Good enough for now" is not sufficient. |
| **Self-merge** | You may not merge your own PR. At least one approved review from another team member is required regardless of PR type. |
| **Stale approvals** | A `push` to the branch after an approval invalidates the approval (GitHub setting: "Dismiss stale pull request approvals when new commits are pushed"). |

### 3d. Merge strategy

| Rule | Detail |
|------|--------|
| **Strategy** | **Squash and merge** only — enforced by GitHub branch-protection. Merge commits and rebase-and-merge are disabled. |
| **Commit message** | The squash commit message is the **PR title** in Conventional Commits format. Clean up the body before merging — remove auto-generated commit list noise. |
| **Branch deletion** | GitHub auto-deletes the head branch on merge. Do not re-use deleted branches. |

---

## 4. End-to-End Gate Summary

The table below shows every quality gate in the order it is encountered, from local
development to production merge.

```
Developer machine                    CI (every PR push)              GitHub branch protection
─────────────────                    ──────────────────              ────────────────────────
1. Pre-commit (Husky)                5. Lint (frontend + backend)    9.  All required CI checks ✅
   • ESLint on staged files          6. Type-check (frontend +        10. Minimum approvals met
   • Conventional Commits msg fmt       backend)                     11. Branch up-to-date with
                                     7. Tests (frontend + backend)        main (rebase required)
2. Local lint (npm run lint)         8. Build (frontend + backend)   12. Squash-and-merge only
3. Local type-check                  ↕
4. Local tests                    On infra/ changes:
                                    + cdk synth gate
                                  On API contract changes:
                                    + types-freshness gate
```

A PR is **not eligible for merge** until every gate at all three stages is satisfied.

---

## 5. Common Failure Modes and Remediation

| Failure | Likely cause | Remediation |
|---------|-------------|-------------|
| `eslint` reports "no warnings" expectation failed | `--max-warnings 0` — even warnings block CI | Fix all warnings; do not suppress with `// eslint-disable` without a documented reason in the PR |
| `tsc --noEmit` fails on `api-types.gen.ts` | Backend API contract changed but types not regenerated | Run `cd frontend && npm run generate:types` and commit the updated file |
| Vitest / Jest fails only in CI | Test depends on local state, time, or environment variable | Make the test deterministic; use `vi.useFakeTimers()` or seed the value in the test setup |
| Playwright E2E fails in CI | Services not fully started before spec runs | Check `playwright.config.ts` `webServer` startup timeout; verify health endpoints are polled before tests run |
| `cdk synth` fails | CDK construct property type changed after L2 construct upgrade | Run `cd infra && npm ci && npx cdk synth` locally to reproduce; fix the construct configuration |
| Branch protection: "branch is out of date" | Another PR merged to `main` after your last rebase | `git fetch origin && git rebase origin/main` and force-push your branch |
| "Changes requested" — stale approval dismissed | Pushed new commits after approval | Address review comments; re-request review after the push |
| PR blocked: "required reviewers not satisfied" | Security/infra/breaking-change PR without the correct owner approval | Add the appropriate owner (security owner, infra owner, or engineering lead) as a reviewer |
| Pre-commit hook bypassed with `--no-verify` | Emergency or tooling issue | The PR description **must** note the bypass, the reason, and confirm CI passed instead |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Full contributing guide — branching, commits, coding standards, PR process, issue reporting, security disclosure, release process |
| [`docs/getting-started.md`](getting-started.md) | Local environment setup, running services, test commands |
| [`docs/architecture.md`](architecture.md) | Component model, data flows, AWS topology |
| [`docs/decision-log.md`](decision-log.md) | ADRs and DSNs — rationale for every major technical decision |
| [ADR-010](decision-log.md#adr-010) | CI/CD pipeline design — GitHub Actions + OIDC federation |
| [DSN-002](decision-log.md#dsn-002) | API type generation from OpenAPI spec — `generate:types` gate |
