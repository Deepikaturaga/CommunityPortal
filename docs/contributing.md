- [ ] `IF-017` EventBridge events emitted only on correct state transitions (not on draft save) — see `backend/app/domain/events.py`
- [ ] Structured log lines do not include passwords, tokens, PII beyond user ID (NFR-009) — verified by `backend/tests/security/test_log_audit.py`
- [ ] No mypy `type: ignore` (backend) or `any` TypeScript (frontend) without a justified inline comment
- [ ] Alembic migration is backward-compatible if the PR touches the DB schema
- [ ] IaC plan output (`tofu plan -var-file=beta.tfvars`) attached as PR comment for any `infra/` change
# Contributing

> This guide covers the **backend** (Python 3.12 / FastAPI / pytest) and **frontend** (React / Vite / Vitest) in a two-directory repository layout. Backend code lives under `backend/`; frontend code under `frontend/`.

> See [Getting Started](./getting-started.md) for the full local development setup guide and [Decision Log](./decision-log.md) for open decisions that gate production lock-in.

---

- **Backend:** Ruff lint + mypy strict type-checking enforced in CI (`cd backend && ruff check . && mypy`). No lint or type errors on merge.
- **Frontend:** ESLint (strict) + `tsc --noEmit` enforced in CI. No errors or warnings (`--max-warnings 0`).
- **Python types:** mypy strict mode (`backend/pyproject.toml [tool.mypy]`). No `type: ignore` without a justified inline comment.
- **Comments:** Every public Python function/class must have a docstring. Every exported TypeScript symbol must have a JSDoc comment.
- **Tests:** New features require unit tests. Any change to an auth or authorization path requires an explicit negative test (access must be denied — VER-004 pattern). Target: 80% line coverage per service.
- **Secrets:** Never commit secrets, tokens, passwords, or connection strings. Use `.env.example` placeholders only. CI secret scan (`.secrets.baseline`) will block any detected secret.
- **Logging:** Use structured JSON logging via `backend/app/core/logging.py`. Never log passwords, tokens, PII beyond user ID, or raw request bodies containing sensitive data (NFR-009).
- **Migrations:** Alembic migrations must be backward-compatible. No destructive schema changes (column drops, renames) without a two-phase migration (add → migrate data → drop in separate PRs). Migration scripts live in `backend/alembic/versions/`.
Every new router in `backend/app/routers/` and `backend/app/services/*/router.py` must use the deny-by-default auth dependency from `backend/app/auth/dependencies.py` before any route handler. Admin endpoints must additionally enforce admin-role checks via `backend/app/services/admin/` middleware. Failing to do this will cause VER-004 tests to fail.
Any endpoint that accepts free-text user content (threads, replies, posts, comments, KB articles) must pass the body through the server-side sanitiser before persistence (`backend/app/kb/sanitizer.py` for KB; equivalent patterns for discussion/posts). Never persist unsanitized user input (DEC-001/DEC-003).
Endpoints that publish `IF-017` events (thread create, post publish, KB approve, comment create) must emit the EventBridge event via `backend/app/domain/events.py` or `backend/app/services/kb/events.py` atomically with the DB write. Use transactional outbox or confirm event-after-commit to avoid partial failures.
| Unit | pytest (`backend/`) | Every new function / module |
| Integration | pytest + httpx (`backend/`) | Every new FastAPI route; must include at least one negative authorization test (403/401/404) |
| Frontend unit | Vitest (`frontend/`) | Every new React component or utility |
| Validation suite | pytest per domain (`backend/tests/{domain}/`) | Each phase produces a CI-gated suite per the phase plan |
| Identity / Session | `backend/tests/identity/` | PHASE-013 | VER-001, VER-005–008, VER-012, VER-016, VER-017 |
| Profile / Admin / Taxonomy | `backend/tests/profile_admin/` | PHASE-019 | VER-004, VER-021 |
| Discussion / Moderation | `backend/tests/test_moderation.py`, `backend/tests/routers/` | PHASE-024 | VER-002, VER-020 |
| Posts | `backend/tests/posts/` | PHASE-028 | VER-002, VER-010, VER-020 |
| Knowledge Base | `backend/tests/test_kb_articles.py`, `backend/tests/services/kb/` | PHASE-032 | VER-002, VER-004, VER-010 |
| Search | `backend/tests/search/` | PHASE-036 | VER-003, VER-009 |
| Notifications | `backend/tests/test_notification_router.py` | PHASE-039 | VER-024 (JRN subset) |
| Admin Dashboard | `backend/tests/test_admin_dashboard.py`, `frontend/tests/admin-dashboard/` | PHASE-041 | VER-004 |
| Accessibility | `frontend/tests/a11y/` | PHASE-044 | VER-022 |
| Responsive | `frontend/tests/a11y/accessibility-responsive.spec.ts` | PHASE-044 | VER-023 |
| E2E Critical Journeys | `backend/tests/e2e/` | PHASE-045 | VER-024 |
# Backend — from backend/
pytest                                       # all unit + integration tests
pytest tests/e2e/                            # E2E journeys (requires running stack)
pytest tests/security/                       # security tests (IaC scan, log audit, pipeline gates)
pytest tests/test_csrf_middleware.py tests/test_security_headers.py  # CSRF / security header tests

# Frontend — from frontend/
npm test                                     # Vitest unit/component tests
npx playwright test tests/a11y/              # accessibility scan (requires running stack)
## Development Workflow

1. Branch from `main` using `feature/{story-id}-short-description` (e.g. `feature/STORY-008-session-store`)
2. Keep PRs focused — one story or fix per PR
3. All PRs require:
   - Passing CI (unit tests, integration tests, lint, type-check, SCA scan, secret scan)
   - At least one reviewer approval
   - No new secrets or hardcoded credentials (checked by the CI secret-scanning step)
4. Squash-merge into `main`
5. Delete the feature branch after merge

---

## Branch Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Feature / story | `feature/{story-id}-description` | `feature/STORY-014-profile-crud` |
| Phase / task | `phase/{phase-id}-description` | `phase/PHASE-020-discussion-thread-crud` |
| Task slice | `task/{task-id}-description` | `task/TASK-032-discussion-thread-crud` |
| Bug fix | `fix/{issue-id}-description` | `fix/123-token-expiry-off-by-one` |
| Hotfix (prod) | `hotfix/{issue-id}-description` | `hotfix/456-ses-timeout` |
| Infrastructure | `infra/{story-id}-description` | `infra/STORY-001-vpc-baseline` |
| Documentation | `docs/{topic}` | `docs/runbook-update` |

---

## Commit-Slice Model

The project is broken into 23 mergeable **slices** (SLICE-001–SLICE-023). Before raising a PR, confirm which slice it belongs to and that its prerequisite slices are already merged into `main`. See the [Decision Log — Commit-Slice to Story Map](./decision-log.md#commit-slice-to-story-map) for the full dependency table.

Key rules:
- **SLICE-016 is a hard convergence point** — it cannot merge until SLICE-011 (discussion), SLICE-013 (posts), and SLICE-015 (KB) are all in `main`.
- **SLICE-010 / SLICE-012 / SLICE-014** (Discussion/Posts/KB build phases) are intentionally independent and can be worked concurrently once SLICE-009 merges.
- **SLICE-018 / SLICE-019 / SLICE-020** (Notifications/Dashboard/Hardening) may merge in any order once their respective prerequisite slices are in `main`.

---

## Coding Standards


---

## Service-Level Implementation Rules

### Authorization

### Content Input

### Event Emission

---

## Testing Requirements

| Level | Tool | When Required |
|-------|------|--------------|
| E2E | TASK-062 / PHASE-045 | Critical journeys JRN-001–009 (requires running stack) |
| Security | TASK-059 / PHASE-043 | CSRF, header hardening, auth bypass, injection, SSRF |
| Accessibility | TASK-060 / PHASE-044 | Any UI component (WCAG 2.1 AA, axe-core) |

### Validation Suite Locations

| Domain | Test Path | Gate Phase | Key VER IDs |
|--------|-----------|-----------|------------|

Run tests locally before pushing:

```bash
```

---

## Security Checklist for PRs

Before marking a PR ready for review, confirm all items below:

- [ ] No secrets, tokens, passwords, or connection strings committed (CI secret scan will also check)
- [ ] Auth middleware registered on every new protected route (deny-by-default, TASK-022 pattern)
- [ ] At least one negative authorization test for every new endpoint (VER-004 pattern)
- [ ] Free-text user input passed through server-side sanitiser before persistence (DEC-001/DEC-003 pattern)

---

## Open Decisions Gate

The following open decisions gate production lock-in for specific phases. **Do not unilaterally resolve an open decision in a feature PR.** Confirm resolution in [Decision Log](./decision-log.md) and [Design](./design.md) §10 first.

| Decision | Blocks | Resolution Required Before |
|----------|--------|--------------------------|
| DEC-001 | Server-side sanitiser library | PHASE-020 (discussion) ships to prod |
| DEC-002 | Notification channel scope beyond SES + in-portal | PHASE-038 ships to prod |
| DEC-003 | Sanitiser HTML whitelist config | PHASE-020 ships to prod |
| DEC-004 | Avatar/media file size limits | TASK-026 prod sizing |
| DEC-005 | Compute platform final lock-in | PHASE-001 prod apply |
| DEC-006 | OpenSearch cluster sizing | PHASE-033 prod apply |

---

## Infrastructure Changes

- All infrastructure changes must go through IaC (OpenTofu). No manual AWS console changes (no clickops).
- Run `tofu plan -var-file=beta.tfvars` and include the plan output as a PR comment for all `infra/` changes.
- Production IaC changes require a second reviewer approval and a reviewed `tofu plan` before `tofu apply`.
- Destructive resource changes (database replacements, VPC changes) require a change-freeze notification to the team.

---

## Issue Reporting

Open a GitHub Issue with:

- **Title:** `[BUG]` or `[FEATURE]` prefix followed by a concise description
- **For bugs:** steps to reproduce, expected behaviour, actual behaviour, environment (beta/prod/local), relevant log `correlationId`
- **For features:** use case and acceptance criteria; reference the relevant story ID (STORY-xxx) if applicable
- **Security vulnerabilities:** do **NOT** open a public issue — follow the responsible disclosure process (TBD — contact the security owner directly)
