---

## Phase 1/3

The workspace is completely empty. This task references **PHASE-010** as a dependency and requires `services/*/middleware/authn.*` — but without authoritative context (requirements doc, design spec, acceptance criteria for AC-033.x, interface contracts, existing PHASE-010 output, or the canonical app root) I cannot safely guess the domain model, service layout, JWT library, settings keys, or route structure.

---

## BLOCKED: authoritative context missing

**Reason (per §1 & §2 of the Implementation Contract):**

| Missing item | Why it blocks TASK-022 |
|---|---|
| **PHASE-010 output** | TASK-022 depends on PHASE-010 (`DEPENDS ON: PHASE-010`). The canonical ASGI entrypoint, app package layout, settings module, and router registration that the middleware must attach to do not exist on disk. Writing middleware in isolation against an unknown app root produces dead code. |
| **Requirements doc (FR-033 text)** | "Deny-by-default auth middleware on every protected route" — *which* routes are protected, *which* are public, and *what* counts as authenticated is defined only by FR-033's full specification. Without it I cannot write the `UNPROTECTED_PATHS` allow-list, the token extraction logic, or the rejection response shape. |
| **Acceptance criteria AC-033.x** | The exit criteria reference AC-033.x but the acceptance criteria are not supplied. Each AC row becomes a test case; without them the test suite cannot be written and the phase cannot close. |
| **Canonical service layout** | The path pattern `services/*/middleware/authn.*` implies a multi-service monorepo, but zero files exist. I cannot determine: how many services exist, their names, whether they share a base package or are independent ASGI apps, which dependency manifest / lockfile is canonical, or what Python package/import path to use. |
| **JWT / auth library** | Token format (JWT bearer, session cookie, API key), library (`python-jose`, `PyJWT`, `authlib`), signing algorithm, issuer, audience, and key source are unspecified. Choosing the wrong one creates a hard-to-refactor security boundary. |
| **Response envelope / error shape** | The shape of a 401/403 response must match the global error handler established in PHASE-010. Without it the middleware emits an incompatible error response. |

**What is needed to unblock:**

1. The PHASE-010 file output (or a `repo_snapshot`) — even a manifest of paths suffices.
2. The full text of **FR-033** and its acceptance criteria **AC-033.x**.
3. The list of service names under `services/`.
4. The auth library + token format decision.
5. The canonical error-response envelope spec.

Please supply the above and I will implement TASK-022 in full (middleware, allow-list, dependency injection, tests) immediately.

---

## Phase 2/3

The workspace is still empty. Before writing a single line, I must apply the Implementation Contract gates. Here is the full assessment:

---

# Phase 2/3 — Gate Assessment

## Task Routing & Blocking Analysis

### TASK-023 — Post-login redirect-to-original-URL logic
**Type declared: Frontend**
**Files: `web/src/routing/guards.*`**

Per Implementation Contract §3 (Enforce technology and task boundaries):

> For frontend, infrastructure-as-code, documentation, penetration-testing, or deployment-only tasks, emit `ROUTE TO SKILL: <task ID> — <required capability>` and no substitute implementation.

`ROUTE TO SKILL: TASK-023 — Frontend routing / JavaScript guard implementation`

This skill implements only FastAPI/Python backend tasks. `web/src/routing/guards.*` is a frontend artifact. No stub, no placeholder, no route shell — implementing it here is a contract violation.

---

### Unnamed backend task (auth middleware / VER-004)

| Blocking condition | Detail |
|---|---|
| **TASK-017 output missing** | The task declares `Depends On: TASK-017`. TASK-017 has not been delivered and zero files exist in the workspace. The canonical ASGI entrypoint, app package, settings module, and router registration that middleware must attach to are absent. Writing middleware against a nonexistent app root produces dead code that cannot be registered, imported, or tested. |
| **No task ID supplied** | The task block is missing an ID. Traceability (§5) requires mapping every acceptance criterion to a task ID and ≥1 verification step. Without an ID the checkpoint ledger and traceability table cannot be completed. |
| **Acceptance criteria underspecified** | "Unauthenticated request to protected route → redirect/401 to `/login`" is one half-sentence. Missing: the protected-route list / allow-list (which paths are public?), whether the response is a `401 JSON` body or an HTTP `302` redirect (these are mutually exclusive behaviors with different client contracts), the token format (Bearer JWT? cookie? API key?), the JWT library and signing algorithm pinned in the lockfile, the issuer/audience claims to validate, and the error envelope shape. |
| **VER-004 not specified** | The validation step is cited by ID but its definition is not supplied. A phase cannot close without runnable verification commands (§9). |
| **No canonical app root** | Workspace is empty. `services/*/middleware/authn.*` pattern implies a multi-service layout but zero services, manifests, or entrypoints exist. The structural pre-flight (§2) cannot pass. |
| **Dependency manifest / lockfile absent** | Cannot resolve JWT library version, cannot confirm Pydantic v1 vs v2, cannot run `pip install`, cannot type-check, cannot run tests (§9 step 1). |

`BLOCKED: authoritative context missing (TASK-017 output, task ID, canonical app root, requirements FR-033 full text, AC-033.x criteria, VER-004 definition, JWT library + lockfile)`

---

## Summary

| Task | Disposition | Reason |
|---|---|---|
| *(unnamed)* auth middleware | **BLOCKED** | Depends on TASK-017 (not delivered); no canonical app root; AC/VER underspecified |
| TASK-023 | **ROUTE TO SKILL: Frontend** | `web/src/routing/guards.*` is a frontend artifact; out of scope for this skill |

**No files were written.** Writing against an empty workspace with no dependency chain satisfies none of the acceptance criteria and would produce unregisterable, untestable dead code — a harder problem than starting clean once the blockers are resolved.

### To unblock Phase 2/3 backend work, provide:
1. **TASK-017 delivered output** (the canonical `backend/` layout, ASGI entrypoint, settings module, dependency manifest + lockfile)
2. **A task ID** for the middleware task
3. **FR-033 full text** — specifically the public-path allow-list and the rejection response contract (`401` JSON vs `302` redirect)
4. **AC-033.x acceptance criteria** (each row becomes a test case)
5. **VER-004 definition** (the exact verification command/assertion)

---

## Phase 3/3

**BLOCKED: authoritative context missing — Phase 3/3 cannot proceed.**

The workspace is still completely empty. Phase 3/3 asks for an E2E test, but writing one requires all of the following to already exist on disk (typically delivered by Phases 1 and 2):

| Missing prerequisite | Why it blocks the E2E test |
|---|---|
| **No ASGI app / entrypoint** | `ASGITransport` / `TestClient` needs a real `app` object to import. There is nothing at `backend/app/main.py` or any equivalent path. |
| **No auth middleware** | Phase 1 was BLOCKED — `services/*/middleware/authn.*` was never written. The E2E test cannot exercise what does not exist. |
| **No route definitions** | Protected vs. public routes are unknown; without them the test cannot assert "route X requires a valid token" vs. "route Y is public". |
| **No requirements / acceptance criteria (AC-033.x)** | Each AC row becomes a test case. Without the AC list I cannot write assertions — only fabricate them, which is a defect under §4 (domain-coverage gate) and §7 (no placeholder implementations). |
| **No dependency manifest** | `pytest`, `httpx`, `pytest-asyncio`, JWT test-fixture library versions are unknown. A `pyproject.toml` / `requirements.txt` must exist before `pip install` and test execution are possible. |
| **No JWT / token fixtures** | Signing key, algorithm, issuer, audience, and token shape are required to build valid and invalid token fixtures for the test matrix. |

**What must happen before Phase 3/3 can be written:**

1. Phase 1 must be unblocked — supply the missing authoritative context listed in the Phase 1 block report (requirements text for FR-033, acceptance criteria AC-033.x, canonical service/package layout, JWT library + algorithm choice, PHASE-010 output or equivalent bootstrap).
2. Phase 2 (middleware + app wiring) must be committed and passing lint/type-check/unit tests.
3. The E2E test file can then be written against the real app object, real route table, and real AC rows.

**Completed:** *(none)*
**Blocked:** Phase 3/3 — E2E test — all prerequisites absent; workspace is empty.
**Deferred:** Resume after Phases 1 and 2 close with verified, committed output.