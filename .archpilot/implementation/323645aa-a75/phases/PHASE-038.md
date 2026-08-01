---

# Implementation: Notification Dispatch Worker (PHASE-038 / TASK-054)

## Framework Target

N/A — this task targets **backend worker infrastructure**, not the frontend.

## Routing

> **ROUTE TO SKILL: TASK-054 — Backend / AWS Lambda + SQS worker (Node.js/TypeScript server-side)**

TASK-054 requires:

| Signal | Evidence |
|---|---|
| **Type** declared as `Backend` in the task spec | "Type: Backend" |
| Target files are `workers/notifications/dispatch.*` — a server-side Lambda/SQS consumer | Outside `frontend/` entirely |
| Requires SES integration, SQS event mapping, opt-out enforcement, and in-portal fallback write — all server-side concerns | IF-012, IF-017, AC-029.2 |
| Integration test with mocked SES failure is a backend test concern | "Validation: Integration test with mocked SES failure" |

---

## Why this cannot be implemented here

Per the **Frontend Skill Implementation Contract §4**:

> Implement only frontend tasks here. For backend, IaC, docs, or deployment tasks emit `ROUTE TO SKILL: <task ID> — <required capability>` and no substitute implementation.

Writing `workers/notifications/dispatch.*` from this skill would:

1. Place server-side Lambda/SQS code under `frontend/`, violating the monorepo layout contract (§1a).
2. Introduce backend AWS SDK dependencies (`@aws-sdk/client-ses`, `@aws-sdk/client-sqs`) into the frontend bundle boundary.
3. Create a false build/type-check pass — the frontend toolchain (`next build` / `tsc` scoped to `frontend/tsconfig.json`) cannot verify Lambda handler correctness, SQS event shapes, or SES fallback logic.
4. Produce untestable integration behavior: SES mock/fallback assertions require a backend test runner with AWS SDK mocks, not Jest + React Testing Library.

---

## What the receiving skill needs

When this is routed to the **Backend Worker skill**, pass the following context:

| Item | Detail |
|---|---|
| Interface contract | IF-017 (SQS event schema), IF-012 (notification dispatch interface) |
| Acceptance criteria | AC-029.2: opt-out honored; SES failure → in-portal only, no user-facing error |
| Infra dependency | SQS queue ARN + Lambda role from PHASE-037 (TASK-053) |
| Test requirement | Integration test: mock `@aws-sdk/client-ses` `SendEmailCommand` to throw → assert in-portal notification record written, no exception propagated to caller |
| AWS constraint | SES and SQS must remain within approved AWS region; no cross-provider fallback (aws_only guardrail active) |
| Security | Opt-out check must be server-side before any SES call; no opt-out state trusted from the SQS message payload itself (broken-access-control risk) |

---

## Completed / Blocked / Deferred

| Status | Task | Reason |
|---|---|---|
| **Routed** | TASK-054 | Backend Lambda/SQS worker — outside frontend skill boundary |

**Deferred (pending backend skill execution):** AC-029.2, IF-012, IF-017 validation, SES fallback integration test.