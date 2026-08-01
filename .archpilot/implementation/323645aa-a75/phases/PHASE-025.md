---

## Phase 1/3

The workspace is completely empty and no authoritative context documents are accessible. Per the implementation contract (§1 and §4), I cannot proceed safely without the required context. Let me clearly state what is missing:

---

## BLOCKED: authoritative context missing

**Reason:** The workspace contains **zero files**, and no authoritative context documents are accessible for any of the referenced IDs. Before I can implement PHASE-025 / TASK-039, the following artefacts are required:

---

### Missing Context (required before any code is written)

| Reference ID | Required artefact | Why it is needed |
|---|---|---|
| **PHASE-018** | Prior phase output | PHASE-025 `Depends On` PHASE-018 — the canonical app entrypoint, DB models, Alembic chain, settings module, auth layer, and router registration must already exist |
| **COMP-004** | Component specification | Defines the exact post/draft component behaviour, fields, states, and rules |
| **IF-005** | Interface contract | Defines route paths, HTTP methods, request/response schemas, status codes, and auth requirements for the post/draft API |
| **AC-016.x** | Acceptance criteria | The testable exit criteria that determine when TASK-039 is complete |
| **STORE-004** | Storage/DB store spec | Defines the `posts` table/model schema: columns, indexes, FK relations, enums (`draft`/`published`/etc.), constraints |
| **Sanitization spec** | Requirements doc | Defines which HTML/Markdown elements to allow or strip, which library to use, and what the attack surface is (XSS policy, allowed tags, etc.) |

---

### Structural pre-flight failures

The canonical root is unknown because the workspace is empty:

- No `backend/app/main.py` (ASGI entrypoint)
- No `backend/pyproject.toml` / `requirements.txt` (dependency manifest + lockfile)
- No `backend/alembic.ini` / `backend/alembic/` (migration chain)
- No `backend/app/core/config.py` (settings module)
- No existing models, auth layer, or registered routers to extend

Writing code against an empty workspace without the above would **invent** domain models, routes, schema shapes, and behaviour — violating the contract and producing untraceable output.

---

### What is needed to unblock

Please supply **any one** of the following:

1. **The PHASE-018 output** (the already-written backend files from the prior phase), **plus** COMP-004, IF-005, AC-016.x, and STORE-004 documents — then I will implement TASK-039 against the canonical structures.
2. **A `repo_snapshot`** (file tree with contents) of the existing backend, plus the above specs.
3. **A combined requirements + design doc** covering the above IDs so the domain model, interface contract, and acceptance criteria can be derived from it.

Once that context is provided, I will:
- Read all relevant existing files before touching them
- Extend the canonical `posts` model + Alembic migration
- Implement the service layer with server-side sanitization behind a configurable adapter
- Wire up the router and register it on the canonical app
- Write focused unit + integration tests keyed to every AC-016.x criterion
- Run lint, type-check, and pytest and report real output

---

## Phase 2/3

## BLOCKED: prerequisite phases not implemented and authoritative context still absent

The workspace remains **completely empty**. Phase 1 was blocked and produced zero files; Phase 2 inherits the same blocking conditions. I cannot proceed safely.

---

### Why this phase cannot run

| Blocking condition | Detail |
|---|---|
| **Depends On: TASK-030 / TASK-039 not satisfied** | Both tasks were part of Phase 1, which was blocked. There is no canonical app, no `backend/` tree, no models, no Alembic chain, no auth layer, and no router for `events.*` code to extend. |
| **IF-017 not supplied** | TASK-040 must publish an `IF-017` event on publish state transition. The event schema, broker type (e.g. SQS, SNS, in-process), payload fields, topic/queue name, error/retry policy, and delivery guarantee are all undefined. Writing an `events.py` stub without this contract would produce fabricated, untestable behavior. |
| **COMP-004 / IF-005 still missing** | The post/draft component spec and its API interface contract (routes, states, state-machine transitions) are required to determine *what constitutes a publish transition* — the sole trigger for the TASK-040 event. |
| **AC-016.1/.3 acceptance criteria not supplied** | "Event fires only on publish, not draft save" is the only criterion visible, but the full acceptance criteria set (AC-016.1, AC-016.3) needed to scope and verify this task has never been provided. |
| **Canonical backend root does not exist** | `backend/app/main.py`, `backend/pyproject.toml`, `backend/alembic/`, `backend/app/core/config.py` are all absent. `services/posts/events.*` has nowhere to live. |

---

### What is needed to unblock Phase 2

Please provide **all** of the following before re-submitting:

1. **Phase 1 output** — the fully implemented and committed `backend/` tree (or a repo snapshot showing it exists).
2. **IF-017** — the event contract: event name, schema/payload fields, broker/transport (SNS topic ARN? SQS queue? In-process event bus?), auth/signing requirements, delivery semantics.
3. **COMP-004** — post component spec with the explicit state machine (`draft → published`, any intermediate states, allowed transitions, who may trigger them).
4. **AC-016.1 and AC-016.3** — the full, testable acceptance criteria text.
5. **STORE-004** — posts table schema (columns, status enum values, indexes, FK relations) if not already present in Phase 1 output.

Once these artefacts are available and Phase 1 is verified complete, Phase 2 can be implemented correctly in a single coherent pass.

---

**Completed:** none  
**Blocked:** TASK-040 — prerequisite phases not implemented; IF-017, COMP-004, AC-016.1/.3 not supplied  
**Deferred:** all Phase 2 work pending unblock

---

## Phase 3/3

The workspace is still completely empty — no files were produced by Phase 1 or Phase 2. There is nothing to write integration tests against.

---

## BLOCKED: authoritative context missing (all phases)

Per the implementation contract (§1 and §2), **Phase 3 cannot proceed** because the prerequisite deliverables from Phase 1 and Phase 2 do not exist in the workspace.

### Why this phase is blocked

| Prerequisite | Expected artefact | Status |
|---|---|---|
| Phase 1 | ASGI entrypoint `backend/app/main.py`, settings, Alembic chain, dependency manifest | **Missing — Phase 1 was also BLOCKED** |
| Phase 2 | Domain models, schemas, service layer, routers (the code-under-test) | **Missing — no files in workspace** |
| Acceptance criteria (AC-016.x) | Testable exit criteria to write assertions against | **Never supplied** |
| Interface contract (IF-005) | Route paths, HTTP methods, status codes, request/response shapes | **Never supplied** |
| STORE-004 / COMP-004 | DB schema and component behaviour to validate | **Never supplied** |

### What integration tests require (and what is absent)

An integration test suite for a FastAPI backend needs, at minimum:

1. **A running app** — `backend/app/main.py` with `app = FastAPI(...)` → **does not exist**
2. **A database model + migration** — SQLAlchemy models + Alembic chain to create the test schema → **does not exist**
3. **Routes to call** — at least one `APIRouter` registered on the app → **does not exist**
4. **A dependency manifest** — `backend/pyproject.toml` or `requirements.txt` so `pytest`, `httpx`, `pytest-asyncio`, and `SQLAlchemy` can be resolved → **does not exist**
5. **Concrete acceptance criteria** — the expected HTTP status codes, response payloads, and failure cases to assert → **never provided**

Writing test stubs with `# TODO` assertions, fabricated route paths, or invented schema shapes would violate §1 ("No placeholder implementations"), §4 ("Refuse to build endpoints whose entities do not exist in the canonical models"), and §9 ("Never claim complete when any Must criterion is blocked or unverified").

---

### How to unblock all three phases

Please supply the following before re-running:

1. **Authoritative requirements / design document** — component spec (COMP-004), interface contract (IF-005), acceptance criteria (AC-016.x), storage spec (STORE-004), and sanitisation policy.
2. **Existing backend files** (repo snapshot or zip) **if Phase 1 and Phase 2 were completed elsewhere** — paste or attach the file tree so Phase 3 can read the real code and write targeted tests against it.
3. **Confirmed tech-stack versions** — `pyproject.toml` / `requirements.txt` lockfile so library APIs (FastAPI, SQLAlchemy, Pydantic, pytest-asyncio) can be resolved to exact versions before any code is generated.

Once those artefacts are available, Phase 3 can produce a complete, runnable integration-test suite covering all acceptance criteria.

**Completed:** *(none)*
**Blocked:** Phase 3 / integration tests — prerequisite workspace empty, authoritative context never supplied
**Deferred:** *(none — cannot defer what cannot be scoped)*