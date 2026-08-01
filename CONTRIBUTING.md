# Contributing Guide

> Thank you for taking the time to contribute! This document covers everything you need
> to get a change from idea to merged PR: branching strategy, commit conventions, coding
> standards, testing requirements, the pull-request process, and how to report issues or
> security vulnerabilities.
>
> **Before you start:** make sure your local environment is fully working. Follow
> [`docs/getting-started.md`](docs/getting-started.md) if you have not already done so.

---

## Table of Contents

1. [Code of Conduct](#1-code-of-conduct)
2. [Branching Strategy](#2-branching-strategy)
   - [2a. Branch naming](#2a-branch-naming)
   - [2b. Branch lifecycle](#2b-branch-lifecycle)
   - [2c. Long-running branches](#2c-long-running-branches)
3. [Commit Conventions](#3-commit-conventions)
   - [3a. Conventional Commits format](#3a-conventional-commits-format)
   - [3b. Commit scope reference](#3b-commit-scope-reference)
   - [3c. Breaking changes](#3c-breaking-changes)
   - [3d. Commit hygiene](#3d-commit-hygiene)
4. [Coding Standards](#4-coding-standards)
   - [4a. TypeScript](#4a-typescript)
   - [4b. React and Next.js](#4b-react-and-nextjs)
   - [4c. Backend (Express)](#4c-backend-express)
   - [4d. Database and Prisma](#4d-database-and-prisma)
   - [4e. CSS and Tailwind](#4e-css-and-tailwind)
   - [4f. Testing](#4f-testing)
   - [4g. Security](#4g-security)
   - [4h. Accessibility](#4h-accessibility)
5. [Pull Request Process](#5-pull-request-process)
   - [5a. Before you open a PR](#5a-before-you-open-a-pr)
   - [5b. PR title and description](#5b-pr-title-and-description)
   - [5c. PR checklist](#5c-pr-checklist)
   - [5d. Review requirements](#5d-review-requirements)
   - [5e. Merging](#5e-merging)
6. [Issue Reporting](#6-issue-reporting)
   - [6a. Bug reports](#6a-bug-reports)
   - [6b. Feature requests](#6b-feature-requests)
   - [6c. Questions and discussions](#6c-questions-and-discussions)
7. [Security Vulnerability Disclosure](#7-security-vulnerability-disclosure)
8. [Architecture and Design Decisions](#8-architecture-and-design-decisions)
9. [Release Process](#9-release-process)
10. [Getting Help](#10-getting-help)

---

## 1. Code of Conduct

All contributors are expected to behave professionally and respectfully. We follow the
[Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
Violations can be reported privately to the project maintainers. Harassment, personal
attacks, and discriminatory language are grounds for immediate removal from the project.

---

## 2. Branching Strategy

This project uses a **trunk-based development** model with short-lived feature branches.
The `main` branch is always releasable; it is the single source of truth and is directly
deployed to staging on every merge.

### 2a. Branch naming

Use the following prefixes, followed by a short kebab-case description:

| Prefix | Use for | Example |
|--------|---------|---------|
| `feat/` | New features or enhancements | `feat/user-profile-page` |
| `fix/` | Bug fixes | `fix/login-redirect-loop` |
| `chore/` | Tooling, dependency updates, CI config | `chore/upgrade-prisma-5` |
| `docs/` | Documentation-only changes | `docs/update-getting-started` |
| `refactor/` | Code restructuring without behaviour change | `refactor/extract-auth-hook` |
| `test/` | Adding or fixing tests only | `test/add-upload-e2e` |
| `infra/` | Infrastructure-as-Code changes | `infra/add-cloudwatch-alarm` |
| `hotfix/` | Urgent production fixes branched from a release tag | `hotfix/v1.2.4-session-expiry` |

**Rules:**
- Branch names must be all lowercase with hyphens as separators — no spaces, underscores,
  or slashes beyond the prefix separator.
- Include the ticket/issue number where applicable: `feat/PROJ-123-dark-mode`.
- Maximum branch name length: 60 characters.

### 2b. Branch lifecycle

```
main ──────────────────────────────────────────────► (always deployable)
       │                        ▲
       │ git checkout -b        │ squash-merge PR
       ▼                        │
 feat/your-feature ────────────►
 (short-lived: ideally ≤ 3 days)
```

1. **Branch from `main`** — always start from the latest `main`.

   ```bash
   git checkout main
   git pull --ff-only origin main
   git checkout -b feat/your-feature
   ```

2. **Keep branches short-lived** — target ≤ 3 days. Large features should be broken into
   incremental PRs using [feature flags](https://en.wikipedia.org/wiki/Feature_toggle) to
   keep each PR reviewable and mergeable independently.

3. **Rebase before opening a PR** — rebase on `main` (not merge) to keep history linear.

   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Delete the branch after merge** — GitHub is configured to auto-delete head branches
   on PR merge.

### 2c. Long-running branches

There are no long-running release branches. The only permanent branches are:

| Branch | Purpose |
|--------|---------|
| `main` | Trunk — always deployable; auto-deploys to staging on push |

Production is deployed by tagging `main` with a semantic version (see §9).

---

## 3. Commit Conventions

This project follows the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
specification. Commit messages are parsed by the changelog generator and release tooling.

### 3a. Conventional Commits format

```
<type>(<scope>): <short description>

[optional body — explain the *why*, not the *what*]

[optional footer(s) — BREAKING CHANGE, Closes #nn, Co-authored-by]
```

**Rules for the header line:**
- `type` — one of the values in §3b below (lowercase).
- `scope` — one of the values in §3c below (lowercase, optional but encouraged).
- `short description` — imperative mood, lowercase, no trailing period, ≤ 72 characters.
- The full header line (`type(scope): description`) must be ≤ 100 characters.

**Examples:**

```
feat(auth): add session expiry warning banner

fix(api): return 404 instead of 500 for unknown tenant

chore(deps): upgrade next from 14.1.0 to 14.2.3

docs(contributing): add branch naming conventions

refactor(prisma): extract tenant-filter helper to reduce duplication

test(upload): add presigned-url e2e spec

BREAKING CHANGE: removes the /api/v1/legacy endpoint — migrate to /api/v1/resources
```

### 3b. Commit scope reference

| Scope | Area |
|-------|------|
| `auth` | Authentication, session, cookies |
| `api` | Backend Express routes and controllers |
| `db` | Prisma schema, migrations, queries |
| `frontend` | Next.js app (unspecific changes spanning multiple areas) |
| `backend` | Express app (unspecific changes spanning multiple areas) |
| `infra` | AWS CDK, Docker, CI/CD |
| `ui` | Shared UI components |
| `hooks` | Custom React hooks |
| `types` | Generated or shared TypeScript types |
| `deps` | Dependency updates |
| `lint` | ESLint / Prettier config |
| `test` | Test infrastructure (not test cases for a feature — use the feature's scope) |
| `docs` | Documentation |
| `logging` | Structured logging, observability |
| `upload` | File upload / S3 presigned URL flow |

### 3c. Breaking changes

A commit introduces a breaking change when it:
- Removes or renames a public API endpoint.
- Changes the shape of a request or response that the frontend or external consumers depend on.
- Changes an environment variable name or removes a required variable.
- Drops a database column that is still read by the previous application version.

Mark breaking changes in the commit footer:

```
BREAKING CHANGE: <description of what changed and migration steps>
```

Breaking-change commits trigger a **major version bump** in the release. They require an
additional approval from the engineering lead before merging (see §5d).

### 3d. Commit hygiene

- **One logical change per commit.** A commit that fixes a bug, adds a feature, and
  updates documentation should be three commits.
- **Do not commit** generated files (e.g., `api-types.gen.ts`) — they are regenerated in
  CI. Exception: the initial generation commit when the file is first introduced.
- **Do not commit** `.env`, `.env.local`, lockfile changes that are not the result of a
  deliberate `npm install`/`npm ci` run.
- **No `--amend` or force-push on shared branches.** Only rewrite history on your own
  local feature branch before the first push.
- Pre-commit hooks (Husky + lint-staged) run lint and type-check on staged files
  automatically. Fix all errors before committing; use `git commit --no-verify` only in a
  documented emergency.

---

## 4. Coding Standards

The standards below supplement the automated checks (ESLint, Prettier, `tsc --noEmit`).
If a standard conflicts with a linter rule, the linter rule takes precedence (fix the
code, not the rule) unless you have a documented reason to change the rule itself.

### 4a. TypeScript

- **Strict mode is non-negotiable.** Both workspaces have `"strict": true` in `tsconfig.json`.
  Zero `any`, zero `@ts-ignore` without a documented reason in the same line comment, zero
  non-null assertions (`!`) without a proof comment.
- **Model domain data explicitly.** Prefer discriminated unions over boolean flags when
  a value represents one of several states.
  ```ts
  // ✅ Preferred
  type UploadState =
    | { status: 'idle' }
    | { status: 'uploading'; progress: number }
    | { status: 'done'; url: string }
    | { status: 'error'; message: string };

  // ❌ Avoid
  type UploadState = { isUploading: boolean; isDone: boolean; error?: string; url?: string };
  ```
- **Never hand-duplicate server DTOs.** Import types from `frontend/src/lib/api-types.gen.ts`
  (generated from the OpenAPI spec). Opening a PR that adds a manually-written interface
  mirroring a server response shape is a review blocker.
- **Infer return types** on private functions; annotate return types explicitly on exported
  functions and hook signatures.
- **Enums:** prefer `const` objects with `as const` + a derived union type over TypeScript
  `enum` (avoids runtime emit and tree-shaking issues).
  ```ts
  // ✅ Preferred
  export const Role = { Admin: 'ADMIN', Member: 'MEMBER' } as const;
  export type Role = (typeof Role)[keyof typeof Role];

  // ❌ Avoid
  export enum Role { Admin = 'ADMIN', Member = 'MEMBER' }
  ```

### 4b. React and Next.js

- **Server components by default.** Add `"use client"` only when the component requires
  browser APIs, event handlers, `useState`, `useEffect`, or third-party client-only
  libraries. Every `"use client"` addition requires a comment explaining why it is needed.
- **Function components only.** No class components.
- **Hooks at the top level only.** Never call hooks inside conditions, loops, or nested
  functions.
- **No Effects for derived state.** If a value can be computed from props or other state
  during render, compute it inline — do not use `useEffect` + `setState` to derive it.
- **No Effects for event-specific logic.** User interactions belong in event handlers, not
  Effects.
- **Async UI states are mandatory.** Every component that performs an async operation
  must handle all four states: `loading`, `empty`, `error`, and `success`. Use
  `<Suspense>` + `loading.tsx` for server components; use `useQuery` states for client
  components.
- **Stale request cancellation.** Client-side fetch calls within `useEffect` must return
  a cleanup function that calls `controller.abort()`. TanStack Query handles this
  automatically — prefer it over manual `useEffect` for data fetching.
- **No duplicate submissions.** Forms must disable the submit button while a mutation is
  in-flight. Server actions must use `useFormStatus` or similar to track pending state.
- **`cookies()` is server-only.** Never import `next/headers` in a client component or
  a file that could be imported by a client component.
- **No secrets in `NEXT_PUBLIC_*` variables.** Every `NEXT_PUBLIC_*` value is inlined
  into the browser bundle — treat it as fully public.

### 4c. Backend (Express)

- **Validate all inputs at the route level** using a Zod schema before the request reaches
  the controller. The validation middleware must return `400` with a structured error
  envelope (see DSN-006) on schema violations — never let invalid input reach a service
  function.
- **Authentication and authorisation middleware first.** Protected routes must apply the
  auth middleware (`requireSession`) before any controller logic runs. Authorisation
  checks (tenant ownership, role) happen in the controller or a dedicated authorisation
  service — never in the route definition itself.
- **One responsibility per layer:**
  - `routes/` — Express router registration, middleware chaining.
  - `controllers/` — Parse validated request, call service, format response.
  - `services/` — Business logic, database calls via Prisma.
  - `middleware/` — Cross-cutting concerns (auth, validation, error, logging).
  - `utils/` — Pure helper functions with no side effects.
- **No `req.body` access before validation.** Use `req.validated` (set by Zod middleware)
  as the typed, validated input to the controller.
- **Always pass `next(err)` for errors.** Never `throw` inside an async route handler
  without wrapping in `try/catch` → `next(err)`. Use the `asyncHandler` wrapper utility
  to avoid repetitive try/catch:
  ```ts
  router.post('/resource', asyncHandler(async (req, res) => {
    // errors here are forwarded to next(err) automatically
  }));
  ```
- **No `console.log` in application code.** Use the `pino` logger instance exported from
  `src/utils/logger.ts`. Include relevant context fields (userId, tenantId, requestId)
  but **never** include passwords, tokens, cookies, or PII.

### 4d. Database and Prisma

- **Schema changes require a migration.** Never edit the database directly; always update
  `schema.prisma` and run `npx prisma migrate dev` to generate a migration file.
- **Backward-compatible migrations only** (see DSN-007). The pattern is:
  1. Add the new column as nullable, deploy.
  2. Backfill data, deploy.
  3. Make the column non-nullable, deploy.
  4. Drop the old column in a separate PR, deploy.
- **Every multi-step write is a transaction.** Use `prisma.$transaction([...])` or the
  interactive transaction API for any operation that writes to multiple tables.
- **Tenant filter is mandatory** on every Prisma query against a tenant-scoped table
  (see DSN-008). The `enforce-tenant-filter` ESLint rule enforces this; do not disable
  it without security owner sign-off.
- **`$queryRaw` is allowed for complex analytical queries** but must use tagged template
  literals (parameterised) — never string concatenation.
  ```ts
  // ✅ Parameterised raw query
  await prisma.$queryRaw`SELECT * FROM reports WHERE tenant_id = ${tenantId}`;

  // ❌ Never — SQL injection risk
  await prisma.$queryRaw(Prisma.raw(`SELECT * FROM reports WHERE tenant_id = '${tenantId}'`));
  ```

### 4e. CSS and Tailwind

- **Tailwind utility classes are preferred** over custom CSS for layout, spacing, colour,
  and typography. Use the design tokens defined in `tailwind.config.ts` — do not
  hard-code raw colour hex values in classes.
- **Custom CSS (`@apply` or CSS modules)** is acceptable for complex animations,
  third-party component overrides, and patterns that would require more than ~5 utility
  classes inline.
- **No inline `style=` attributes** unless driven by dynamic runtime values (e.g.,
  progress bar width). Static styles belong in Tailwind classes.
- **Dark mode:** components must respect the `dark:` variant. Test in both light and
  dark mode before marking a visual PR as ready for review.
- **Responsive design:** all interactive UI must be usable at 320 px width and above.
  Test on mobile viewport sizes before review.

### 4f. Testing

- **Write tests for behaviour, not implementation.** Tests should describe what the
  system does, not how it does it internally.
- **Co-locate unit tests** with the file they test: `Button.test.tsx` lives next to
  `Button.tsx`. Integration and E2E tests live in `src/__tests__/` and `e2e/` respectively.
- **Test coverage expectations:**
  - New service-layer functions (backend): unit test covering happy path + at least two
    error paths.
  - New API routes (backend): integration test (Supertest) covering auth, validation
    failure, and success response.
  - New UI components (frontend): React Testing Library test covering render, user
    interaction, and accessible name/role.
  - New critical user journeys: Playwright E2E spec.
- **Do not test implementation details.** Avoid asserting on internal state, private
  function calls, or component internals not observable by a user.
- **Mock at the boundary.** Mock the HTTP layer (MSW for frontend tests, Supertest for
  backend integration tests) — do not mock individual modules or Prisma calls except in
  unit tests for the service layer.
- **Tests must be deterministic.** Flaky tests are treated as bugs; a flaky test in CI
  blocks merge just as a failing test does.
- **Test naming:** use `describe` + `it` with human-readable sentences.
  ```ts
  describe('UploadButton', () => {
    it('disables the button while an upload is in progress', async () => { … });
    it('shows an error message when the upload fails', async () => { … });
  });
  ```

### 4g. Security

The following are hard rules; violations block merge without exception:

- **No secrets or credentials in source code, comments, or test fixtures.** Use
  environment variables; use dummy values in tests (e.g., `SESSION_SECRET=test-secret-32-chars-min`).
- **No `localStorage` or `sessionStorage` for auth state.** Session is carried by the
  HTTP-only cookie; client components read auth state from a context populated by a
  server component — never from browser storage.
- **No direct database access from the frontend.** The Next.js service never imports
  `@prisma/client` or constructs a database connection; all data access goes through the
  Express API over the internal network.
- **Input validation before use.** Never use `req.params`, `req.query`, or `req.body`
  values in a database query, file path, or shell command without first passing them
  through a Zod schema and the validated result.
- **No `dangerouslySetInnerHTML`** with untrusted user content. Sanitise with DOMPurify
  or a server-side sanitiser before rendering user-provided HTML.
- **Dependency additions require a justification comment** in the PR description:
  purpose, maintenance status, and licence. Run `npm audit` before adding; do not add
  packages with known high/critical CVEs.

### 4h. Accessibility

- **Semantic HTML first.** Use `<button>`, `<a>`, `<nav>`, `<main>`, `<section>`,
  `<h1>`–`<h6>`, `<label>`, `<input>` with their native roles before reaching for ARIA.
- **Every interactive element must be keyboard-focusable** and have a visible focus
  indicator (do not `outline: none` without a custom replacement).
- **Every form input must have an associated `<label>`** (via `for`/`id` or `aria-label`
  or `aria-labelledby`). Placeholder text is not a label.
- **Error messages must be announced** to screen readers. Use `role="alert"` or
  `aria-live="polite"` on error containers.
- **Images must have `alt` text.** Decorative images use `alt=""`. Informative images
  describe their content concisely.
- **Colour contrast must meet WCAG 2.1 AA**: 4.5:1 for normal text, 3:1 for large text
  and UI components.
- **Run `axe` or Lighthouse accessibility audit** on any PR that adds or modifies UI
  components. Resolve all `critical` and `serious` violations before requesting review.

---

## 5. Pull Request Process

### 5a. Before you open a PR

Run all of the following locally and fix any failures before pushing:

```bash
# From the workspace you changed (frontend/ or backend/ or both):

npm run lint          # ESLint — zero warnings or errors
npm run type-check    # tsc --noEmit — zero errors
npm test -- --run     # unit/integration tests — all pass
npm run build         # production build — exits 0
```

For frontend changes that affect UI:

```bash
cd frontend
npm run test:e2e      # Playwright — run affected specs
```

For infrastructure changes:

```bash
cd infra
npx cdk synth         # CloudFormation synthesis — no errors
npx cdk diff          # preview resource changes — review before opening PR
```

### 5b. PR title and description

**PR title** follows the same Conventional Commits format as commit messages and becomes
the squash-merge commit message:

```
feat(auth): add session expiry warning banner
```

**PR description** must include the following sections (a template is pre-filled by
GitHub when you open a PR):

```markdown
## Summary
<!-- One paragraph explaining what this PR does and why. -->

## Changes
<!-- Bullet list of significant changes. -->

## Testing
<!-- How was this tested? Which test files were added or updated? -->

## Screenshots / recordings (if UI changes)
<!-- Attach before/after screenshots or a screen recording. -->

## Checklist
<!-- See §5c -->
```

### 5c. PR checklist

Copy this checklist into your PR description and check every box before requesting review:

```markdown
- [ ] My branch is based on the latest `main` and has been rebased (no merge commits)
- [ ] Commit messages follow Conventional Commits (§3a)
- [ ] `npm run lint` passes in all changed workspaces
- [ ] `npm run type-check` passes in all changed workspaces
- [ ] `npm test -- --run` passes in all changed workspaces
- [ ] `npm run build` passes in all changed workspaces
- [ ] New or changed behaviour is covered by tests (unit, integration, or E2E as appropriate)
- [ ] No secrets, credentials, or PII have been added to source files or test fixtures
- [ ] No `console.log` statements left in application code
- [ ] API contract changes are reflected in the OpenAPI spec and the generated types are updated
- [ ] Database schema changes include a migration file and follow the backward-compatibility convention (DSN-007)
- [ ] UI changes have been tested in both light and dark mode and at mobile viewport width
- [ ] Accessibility: no new `axe` critical/serious violations
- [ ] Documentation has been updated if this change affects the getting-started guide, architecture doc, or decision log
- [ ] Breaking changes are documented with a `BREAKING CHANGE` footer and migration steps
```

### 5d. Review requirements

| PR type | Minimum approvals | Approver |
|---------|-------------------|---------|
| Standard (feat, fix, chore, docs, refactor, test) | **1** approving review | Any other team member |
| Infrastructure (`infra/` changes) | **2** approving reviews | At least 1 must be the infrastructure owner |
| Security-sensitive (auth, session, IAM, secret management changes) | **2** approving reviews | At least 1 must be the security owner |
| Breaking change (`BREAKING CHANGE` footer) | **2** approving reviews | At least 1 must be the engineering lead |

CI must be **fully green** (lint, type-check, tests, build) before a review is requested.
Reviewers are not expected to review a PR with a failing CI pipeline.

**Review etiquette:**
- Reviewers should respond within 1 business day. If you cannot review within that window,
  reassign or comment to set expectations.
- Distinguish between blocking (`MUST fix`) and non-blocking (`nit:`, `suggestion:`)
  comments. The author may address non-blocking comments at their discretion.
- Approve only when you are satisfied the PR is correct, tested, and safe to merge.
  A PR is not "good enough for now" — it must be ready for production.

### 5e. Merging

- **Squash and merge** is the required merge strategy (enforced by the GitHub branch
  protection rule). This keeps `main` history linear and readable.
- The squash commit message is the PR title (Conventional Commits format). Clean up the
  body to remove noise before merging.
- Do **not** merge your own PR. At least one approved review from someone else is required.
- Delete the branch after merge (GitHub auto-deletes on merge if the setting is enabled).

---

## 6. Issue Reporting

### 6a. Bug reports

Use the **Bug report** issue template on GitHub. Include:

| Field | What to provide |
|-------|-----------------|
| **Summary** | One sentence: what went wrong |
| **Steps to reproduce** | Numbered list of exact steps |
| **Expected behaviour** | What should have happened |
| **Actual behaviour** | What actually happened |
| **Environment** | OS, Node version, browser, app version/commit SHA |
| **Logs / screenshots** | Paste relevant logs (redact any secrets or PII first) |
| **Severity** | `critical` (data loss, security, production down) / `high` / `medium` / `low` |

**Critical and high severity bugs** (data loss, security issues, production outages)
should be flagged immediately in the team's primary communication channel in addition to
opening a GitHub issue. Do **not** report security vulnerabilities in public issues —
see §7.

**Good bug report example:**

```
**Summary:** Logging in with a valid email/password returns 500 instead of setting a cookie.

**Steps to reproduce:**
1. Start the backend and frontend locally (`docker compose up`).
2. Navigate to http://localhost:3000/login.
3. Enter credentials admin@example.com / correct-password.
4. Click "Sign in".

**Expected:** Redirect to /dashboard with an HttpOnly session cookie set.
**Actual:** 500 Internal Server Error. Browser console shows no Set-Cookie header.

**Environment:** macOS 14.3, Node 20.11.0, Chrome 121, commit abc1234.

**Logs:**
[backend] Error: SESSION_SECRET must be at least 32 characters
```

### 6b. Feature requests

Use the **Feature request** issue template. Include:

- **Problem statement:** what user need or pain point this addresses.
- **Proposed solution:** what you'd like to see implemented (be specific).
- **Alternatives considered:** other approaches you thought of.
- **Acceptance criteria:** a bullet list of conditions that would make the feature
  "done" from your perspective.
- **Priority justification:** why this matters relative to current work.

Feature requests are triaged in the weekly team sync and added to the backlog or
milestone as appropriate. A feature request does not guarantee implementation; it
starts a conversation.

### 6c. Questions and discussions

For questions that are not bugs or feature requests (e.g., "how does X work?",
"should we approach Y this way?"), use **GitHub Discussions** rather than Issues.
Keep Issues clean for actionable, trackable work items.

---

## 7. Security Vulnerability Disclosure

**Do not report security vulnerabilities in public GitHub Issues.**

Security vulnerabilities — including authentication bypasses, privilege escalation,
injection vulnerabilities, secret exposure, and data leakage — must be reported privately
to the security owner.

**Responsible disclosure process:**

1. **Email the security owner** at the address listed in `SECURITY.md` (see the
   repository root). If `SECURITY.md` does not exist yet, email the engineering lead
   directly.
2. **Include in your report:**
   - A description of the vulnerability and the component affected.
   - Steps to reproduce or a proof-of-concept (do not exploit production systems).
   - Potential impact and severity assessment.
   - Any suggested mitigations.
3. **Allow 90 days for remediation** before public disclosure (coordinated disclosure
   model). We will acknowledge your report within 2 business days and provide a status
   update within 7 business days.
4. **Do not disclose publicly** until a fix has been deployed and an agreed embargo
   period has passed.

Contributors who responsibly disclose security vulnerabilities will be acknowledged in
the release notes (with their permission).

---

## 8. Architecture and Design Decisions

Significant architectural decisions are recorded in [`docs/decision-log.md`](docs/decision-log.md)
as Architecture Decision Records (ADRs) or Design Notes (DSNs).

**When to open an ADR:**
- You are proposing to change the framework, cloud platform, database, ORM, container
  strategy, or auth mechanism.
- You are introducing a new cross-cutting dependency (a package used by both the frontend
  and backend, or by infrastructure).
- Your change will be difficult or expensive to reverse once implemented.
- A previous ADR's trade-offs are no longer acceptable and you want to supersede it.

**When to open a DSN:**
- You are making an implementation-level choice within the boundaries set by an existing
  ADR.
- The choice has lasting consequences (e.g., logging format, error envelope shape, file
  upload flow) but does not rise to the level of an ADR.

**How to propose a new ADR/DSN:**
1. Open a draft PR that adds the ADR/DSN entry to `docs/decision-log.md` with
   **Status: In Review**.
2. Tag the engineering lead and relevant owners as reviewers.
3. Allow at least 2 business days for feedback before marking as accepted.
4. Set **Status: Accepted** and merge only after the required approvals (same rules as §5d
   for security-sensitive decisions).

Do not implement a decision that contradicts an existing Accepted ADR without first
opening an ADR to supersede it.

---

## 9. Release Process

Releases follow [Semantic Versioning 2.0.0](https://semver.org/):

| Version component | When to bump |
|-------------------|-------------|
| `MAJOR` (x.0.0) | Breaking API change, breaking environment variable change, or breaking DB migration |
| `MINOR` (0.x.0) | New backward-compatible feature |
| `PATCH` (0.0.x) | Backward-compatible bug fix |

**Release steps:**

1. Ensure `main` is green in CI and has been manually verified on staging.
2. Create and push a version tag from `main`:

   ```bash
   git checkout main
   git pull --ff-only origin main
   git tag v1.2.3 -m "v1.2.3"
   git push origin v1.2.3
   ```

3. The CI pipeline detects the `v*` tag and runs the `promote-to-production` workflow,
   which re-tags the staging image and triggers an ECS rolling deploy to production.
4. Monitor the production deploy in the GitHub Actions tab and in CloudWatch. The deploy
   is considered complete when all ECS tasks are healthy and the health endpoint returns
   `200 OK`.
5. Create a GitHub Release from the tag, using the auto-generated changelog. Review and
   clean up the changelog before publishing. Include:
   - A brief summary of what changed.
   - Migration instructions for any breaking changes.
   - Any known issues or follow-up work.

**Hotfixes** (critical production bugs):

```bash
git checkout v1.2.3   # check out the last known-good release tag
git checkout -b hotfix/v1.2.4-description
# ... make minimal fix ...
git tag v1.2.4
git push origin hotfix/v1.2.4-description
git push origin v1.2.4
# open a PR to back-port the fix to main as well
```

---

## 10. Getting Help

| Resource | Purpose |
|----------|---------|
| [`docs/getting-started.md`](docs/getting-started.md) | Local environment setup, running services, troubleshooting |
| [`docs/architecture.md`](docs/architecture.md) | Component model, data flows, AWS topology |
| [`docs/decision-log.md`](docs/decision-log.md) | Why we made each technology and design decision |
| GitHub Discussions | Questions, design conversations, architecture proposals that are not yet PRs |
| GitHub Issues | Bug reports and feature requests (actionable, trackable items) |
| Team chat channel | `#engineering` — day-to-day questions, urgent issues, standup |

If you are stuck for more than 30 minutes on a local setup issue, open a GitHub Discussion
or ask in `#engineering`. Do not spend hours blocked on environment issues — we want
onboarding to be smooth and your feedback improves this guide.

Welcome, and thank you for contributing! 🎉
