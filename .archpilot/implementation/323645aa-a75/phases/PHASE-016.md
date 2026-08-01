---

## Phase 1/3

The only mentions of "activate/deactivate" are in the ArchPilot guardrails/design engine — not in a target application spec. The IDs PHASE-016, TASK-027, COMP-009, IF-011, AC-008.x are **not present anywhere** in this workspace.

---

## BLOCKED: authoritative context missing (requirements | design | acceptance criteria)

Per the **Implementation Contract §1**, I cannot proceed. Here is a precise account of what is missing and why:

---

### What was requested
Implement **PHASE-016 / TASK-027** — Admin Account Management (activate / deactivate / delete) with forced session invalidation, covering component **COMP-009**, interface contract **IF-011**, and acceptance criteria **AC-008.x**.

### What is missing

| Missing artifact | Why it is required |
|---|---|
| **Requirements document** containing COMP-009 | Defines the behavioral contract for account activate / deactivate / delete (who can call it, what state transitions are valid, what "forced session invalidation" means, idempotency rules, audit obligations) |
| **Interface contract IF-011** | Defines the HTTP verb, path, request/response shapes, error codes, and auth scope for the admin account endpoints |
| **Acceptance criteria AC-008.x** | Every testable "must" this phase must satisfy before it can be marked complete |
| **Output of PHASE-011** (declared dependency) | PHASE-011 should have produced the canonical `User` / `Account` model, the auth/session layer, and the Alembic migration chain that this phase extends — none of those files are present in the workspace |
| **`backend/` directory structure** | The entire `backend/` tree is absent; there is no app package, settings module, dependency manifest, or Alembic chain to extend |
| **Data model decisions** | What does an "account" look like? What statuses exist? Which table(s) does activation/deactivation mutate? Is the session store Redis, DB, or JWT? How is "forced invalidation" implemented (token denylist, session table delete, Redis key delete)? |

### What the workspace does contain
The ArchPilot **runtime** source (`/app/src/archpilot/`) — the orchestration platform itself, not the target application being generated. None of those files are the `backend/` of the user's project.

---

### To unblock this phase, please provide:

1. **Requirements / FRD** with COMP-009 fully described (or paste the relevant section).
2. **Interface contract IF-011** (HTTP method, URL, request body schema, response schema, error codes).
3. **Acceptance criteria AC-008.x** (the full list of testable conditions).
4. **Output of PHASE-011** — either the generated files or a summary of what was produced (User model schema, session/auth approach, Alembic head revision ID).
5. **Technology decisions** locked in a prior phase: async ORM (SQLAlchemy async vs SQLModel), session store (Redis / DB / JWT), Python/FastAPI version pinned in lockfile.

Once those are supplied I can immediately produce — in a single tool-writing pass — the complete vertical slice: migration, `AccountStatus` enum extension, service layer with state-machine guard, admin router with authz, forced-invalidation logic, and the full AC-008.x test suite.

---

## Phase 2/3

## BLOCKED: Authoritative Context Still Missing — Phase 2 Cannot Proceed

Per **Implementation Contract §1**, the blocking conditions established in Phase 1 are **unchanged**. Implementing Phase 2 tasks on top of an unresolved Phase 1 block would produce fabricated behavior, not a verified implementation.

---

### Blocking Dependency Chain

```
TASK-028 (Phase 2) — Depends On → TASK-027 (Phase 1, BLOCKED)
TASK-027 (Phase 1)  — Depends On → TASK-021 (Phase 2 note)
                                   + PHASE-011 output (absent from workspace)
```

TASK-028 explicitly lists `Depends On: TASK-027`. TASK-027 was blocked in Phase 1. Nothing in this prompt resolves that block.

---

### Unresolved Blockers (same as Phase 1 — none cleared)

| Blocker | Still Missing? | Why It Blocks Phase 2 |
|---|---|---|
| `backend/` directory / canonical app package | **YES** | Nothing to write code into; no `app/main.py`, no settings, no dependency manifest |
| PHASE-011 output: `User`/`Account` model, session layer, Alembic chain | **YES** | TASK-027 mutates account state + invalidates sessions — both entities must exist before any service logic can be written |
| Requirements for COMP-009 | **YES** | Still don't know what account statuses exist, what state transitions are legal, or what the data model looks like |
| Interface contract IF-011 | **YES** | HTTP verb, path, request/response shapes, and error codes for the admin endpoints are undefined |
| **AC-008.1** full text | **YES** | Told it involves "deactivation invalidates sessions immediately" — but the exact preconditions, scope, and edge cases are unknown |
| **AC-008.2** full text | **YES** | Referenced but content never supplied |
| **AC-008.4** full text | **YES** | Referenced as "403 for non-admin access" — but the auth model, role definition, and enforcement point are unspecified |
| Session invalidation mechanism | **YES** | Redis denylist? DB session table? JWT short-expiry + revocation? Cannot implement VER-004/VER-008 without this decision |
| VER-004, VER-008 test specifications | **YES** | Cannot write verifiable tests for unspecified verification criteria |

---

### What Is Needed to Unblock

Please supply **all** of the following before re-submitting Phase 2:

1. **The output of PHASE-011** — the committed `backend/` tree containing at minimum:
   - `backend/app/main.py` (canonical ASGI entrypoint)
   - `backend/app/models/user.py` (or equivalent Account model with status enum)
   - `backend/app/core/config.py` and `backend/pyproject.toml` (or `requirements.txt`)
   - Alembic `alembic.ini` + `alembic/versions/` chain with the current head revision
   - The session/auth layer (JWT claims, token store, or session table — whichever PHASE-011 chose)

2. **Full text of AC-008.1, AC-008.2, and AC-008.4** — every sub-criterion, not just a summary phrase.

3. **Interface contract IF-011** — HTTP method, URL path, path/query/body parameters, success response shape, all error codes, and required auth scope.

4. **Session invalidation decision** — which mechanism PHASE-011 chose (token denylist table, Redis, DB session rows, JWT `jti` blacklist, etc.) so that "invalidates all sessions immediately" can be implemented correctly against the real store.

5. **Role/permission model** — what constitutes "admin", how it is stored on the User/Account model, and how it is asserted (e.g. a `role` enum, a `is_admin` flag, an RBAC table) so that the TASK-028 middleware can enforce it.

---

**Completed:** —
**Blocked:** TASK-027, TASK-028
**Deferred:** Phase 3 tasks (same dependency chain)

---

## Phase 3/3

## BLOCKED: authoritative context missing (requirements | design | acceptance criteria)

Per **Implementation Contract §1**, I cannot proceed with **VER-004**.

---

### Precise blockers

| Missing artifact | Why it is required |
|---|---|
| **Definition of VER-004** | No requirements document, acceptance criteria, or design artifact defines what VER-004 is — what it validates, what it calls, what it asserts, and what a pass/fail means |
| **Acceptance criteria for VER-004** | No testable "must" conditions are present. Without them I cannot write a meaningful verifier — any code I produce would be invented behavior |
| **Prerequisite implementation (Phases 1 & 2)** | Phase 1 was explicitly **BLOCKED** (missing COMP-009, IF-011, AC-008.x, User/Account model, auth/session layer, Alembic chain, `backend/` tree). Phase 2 is not described. The workspace contains **zero files**. A validation task cannot exist without a subject to validate |
| **`backend/` directory structure** | No app package, dependency manifest, settings module, or test layout exists. There is nothing to run verification against |

---

### What I would need to unblock VER-004

1. The requirements document (or section) that defines VER-004 — what capability or behavior it covers, what the acceptance criteria are (AC-xxx IDs).
2. Confirmation that Phases 1 and 2 were actually implemented — either their file output is present in the workspace, or they need to be re-run first.
3. The interface contract (IF-xxx) and data model decisions the validation exercises.
4. The test layout / runner configuration (pytest config, async settings, database fixture strategy).

---

**Completed:** none  
**Blocked:** VER-004 — authoritative context missing (task definition, acceptance criteria, prerequisite implementation)  
**Deferred:** all remaining work pending context delivery