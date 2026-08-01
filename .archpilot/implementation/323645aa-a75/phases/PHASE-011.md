---

## Phase 1/3

No files exist yet. I need authoritative context before writing anything.

**BLOCKED: authoritative context missing (requirements | design | acceptance criteria)**

Specifically, the following are absent and required before I can implement PHASE-011 / TASK-020:

| Missing Item | Why Needed |
|---|---|
| **FLOW-003** definition | The exact password-reset flow steps, token generation strategy, expiry, delivery channel (email/SMS), and token storage mechanism are unspecified. |
| **AC-005.x / AC-006.x** acceptance criteria | The precise pass/fail conditions I must satisfy are not provided. I cannot verify completion without them. |
| **PHASE-010 outputs** (canonical models, migration chain, app structure, settings module, DB session) | TASK-020 depends on PHASE-010. Without those files in the repo, I cannot extend the canonical app, locate the `UserAccount` model, the existing Alembic head, or the session factory. Writing from scratch would risk duplicate roots and schema drift — a defect per §2. |
| **Canonical ASGI entrypoint & package path** | Required to determine where `services/identity/reset.*` belongs in the `backend/` layout and how to register the new router. |
| **Token storage strategy** | Signed JWT vs. opaque DB-stored token vs. TOTP affects model additions, migration, and security posture. |
| **All-session invalidation mechanism** | Must know whether sessions are tracked in DB (e.g. `UserSession` table from PHASE-010) or via a JWT blocklist to implement invalidation correctly. |
| **Email/notification adapter** | Whether an SMTP service, SES adapter, or stub is available (and its interface) determines how the reset link is dispatched. |

---

### To unblock this phase, please provide:

1. **FLOW-003** – the full password-reset flow spec (steps, token type, expiry, delivery channel).
2. **AC-005.x and AC-006.x** – complete acceptance-criteria text.
3. **PHASE-010 output files** (or a repo snapshot) – canonical models (`User`, `UserSession` or equivalent), Alembic head revision ID, `backend/app/core/config.py`, and `backend/app/main.py`.
4. **Token strategy decision** – signed JWT (stateless) or opaque DB token (revocable)?
5. **Session-invalidation contract** – how sessions are stored and how "invalidate all" is defined.
6. **Notification adapter interface** – existing or expected `send_email` / mailer contract.

Once those are supplied I will proceed with the full vertical slice (model/migration → schema → service → router → tests) under `backend/`.

---

## Phase 2/3

BLOCKED: authoritative context still missing — Phase 2 cannot proceed.

## Why This Phase Cannot Be Implemented

TASK-021 carries two hard `Depends On` entries — **TASK-020** and **TASK-013** — neither of which exists in the repository. Phase 1 was itself blocked for the same root causes. Those blockers have **not been resolved** in this prompt, so all of them carry forward unchanged.

### Inherited blockers (unresolved from Phase 1)

| Blocker | Impact on TASK-021 |
|---|---|
| **PHASE-010 outputs absent** | No `UserAccount` model, no session-store table/schema, no Alembic head to extend, no canonical `backend/` package path, no DB session factory to import |
| **TASK-020 not implemented** | Reset-completion depends on a token that TASK-020 was supposed to create and store; without it there is nothing to validate or consume |
| **TASK-013 not implemented** | Explicit dependency listed in the task; its interface (session-store API) is required to implement "invalidate all sessions" |
| **FLOW-003 undefined** | Token validation logic (signed JWT vs opaque DB token), expiry check, single-use enforcement, and delivery channel are all unknown |
| **Session invalidation mechanism unknown** | Cannot write `session-store.*` without knowing whether sessions live in a DB table, a Redis key-space, a JWT blocklist, or something else |
| **AC-005.2 text truncated / AC-006.x absent** | "All existing sessions invalidated" is the summary, but pass/fail conditions, scope (device? IP? all tokens?), and timing are not specified |
| **Canonical ASGI entrypoint unknown** | Cannot register the new router or locate `services/identity/reset.*` in the layout |

### What is needed to unblock Phase 2

1. **PHASE-010 repository snapshot** — at minimum: `backend/app/models/user.py`, `backend/app/models/session.py` (or equivalent), `backend/alembic/versions/<head>.py`, `backend/app/main.py`, `backend/app/core/config.py`.
2. **TASK-020 implemented and committed** — the reset-token record (or signed-token spec) that TASK-021 will validate and consume.
3. **TASK-013 implemented and committed** — the session-store interface TASK-021 calls to invalidate sessions.
4. **FLOW-003 full spec** — token type, expiry window, single-use flag, validation steps, post-reset actions.
5. **AC-005.2 complete acceptance criteria** — exact pass/fail conditions, scope of invalidation, expected HTTP status codes and response bodies.
6. **AC-006.x** — any additional criteria for the reset-completion endpoint.

Please provide the above and re-submit Phase 2. I will not write placeholder or fabricated implementations against an undefined contract.

---

## Phase 3/3

**BLOCKED: authoritative context missing (requirements | design | acceptance criteria)**

The repository is empty — no files have been written in any phase. I cannot implement VER-008 because:

| Missing Item | Impact on VER-008 |
|---|---|
| **No Phase 1 or Phase 2 outputs** | VER-008 is a *validation* task — it validates something that must already exist. There is nothing to validate. |
| **VER-008 acceptance criteria absent** | The exact verification commands, pass/fail thresholds, coverage targets, and scope of "validation" are undefined. |
| **No canonical app, models, migrations, or tests** | Any verification suite (pytest, alembic check, mypy, ruff) requires a runnable application. No such application exists. |
| **No dependency manifest / lockfile** | Cannot install, type-check, or lint without `pyproject.toml` or `requirements.txt`. |
| **FLOW-003 / AC-005.x / AC-006.x still absent** | The root block from Phase 1 was never resolved; the domain under test remains unspecified. |

---

### What VER-008 would require to proceed

1. **Phase 1 & 2 must be completed first** — the application code, models, migrations, routers, and tests must exist under `backend/` before any validation phase can run.
2. **VER-008 spec** — the exact definition of this verification task:
   - Which test modules / markers to run (`pytest -m …`)?
   - Which type-check scope (`mypy backend/`)?
   - Which lint rules (`ruff check backend/`)?
   - Coverage threshold (if any)?
   - Migration integrity check (`alembic check`)?
   - Smoke/integration endpoint test?
3. **A runnable environment** — a resolvable lockfile, a reachable test database (or in-memory SQLite override), and environment variable defaults (`.env.test`).

---

### To unblock VER-008, please provide:

1. The outputs of Phase 1 and Phase 2 (repo snapshot, or re-run those phases first).
2. The full text of VER-008's acceptance criteria.
3. Confirmation that FLOW-003 / AC-005.x / AC-006.x have been resolved (the original block from Phase 1 remains open).

**Completed:** —  
**Blocked:** VER-008 — no application exists to validate; authoritative context (prior phase outputs + VER-008 acceptance criteria) missing.  
**Deferred:** —