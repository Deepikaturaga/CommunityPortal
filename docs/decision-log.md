>
> **Implementation note:** The delivery was implemented in **Python 3.12 / FastAPI** (backend) and **React 18 / Vite** (frontend), superseding the earlier plan references to "Node.js services (framework pending DEC-005)". DEC-005 is resolved: compute is ECS/Fargate running Python FastAPI containers managed via Poetry/setuptools.
| **Search** | AWS OpenSearch Service — `STORE-007`; client in `backend/app/services/search/opensearch_client.py` | Fully managed; no self-hosted Elasticsearch infra; native IAM auth; rich aggregation/DSL |
| **Auth model** | JWT (signed with `SECRET_KEY`) + Redis-backed session via `SESSION_SIGNING_SECRET`; session store at `backend/services/identity/session_store.py` | Short-lived token limits blast radius; Redis-backed revocation enables immediate invalidation; satisfies EPIC-002 session-invalidation requirements |
| **Content sanitisation** | Server-side sanitiser — `backend/app/kb/sanitizer.py` (KB); applied at API boundary before Aurora write | Client-side sanitisation alone is insufficient; input must be sanitised at the API boundary before persistence (DEC-001/DEC-003) |
| **Backend language / framework** | Python 3.12, FastAPI, Uvicorn — **DEC-005 resolved** | Replaces earlier "Node.js TBD" placeholder. FastAPI provides async-first request handling, Pydantic validation, and auto-generated OpenAPI docs. Managed via Poetry/setuptools (`backend/pyproject.toml`) |
| **Migration toolchain** | Alembic (`backend/alembic/`) | Standard SQLAlchemy migration tool; version scripts in `backend/alembic/versions/`; sync DSN configured via `DATABASE_SYNC_URL` |
# Decision Log

This file records the original intent, requirements summary, key design decisions, open decisions, and the commit-slice delivery model so that future contributors understand why the system was built this way. Full records are preserved in [Requirements](./requirements.md), [Plan](./plan.md), and [Design](./design.md). Epic/phase/task structure is described in the plan. Component IDs (COMP-xxx), store IDs (STORE-xxx), interface IDs (IF-xxx), and verification IDs (VER-xxx) are defined in the design.

---


---

## Sprint Sequence

The project is delivered across nine sprints. Each sprint has a primary goal and a set of merge-ready commit slices.

| Sprint | Phases | Primary Goal | Outcome |
|--------|--------|-------------|---------|
| Sprint 1 | PHASE-001–007 | AWS foundation, CI/CD security gates, edge/WAF, design system, data stores | Verified infra baseline (SLICE-001–004) |
| Sprint 2 | PHASE-008–013 | Identity & session fully implemented and verified | Auth sign-off before any content exposure (SLICE-005–007) |
| Sprint 3 | PHASE-014–019 | Profile, media adapter, admin account/role, taxonomy | Authorization matrix verified (SLICE-008–009) |
| Sprint 4 | PHASE-020, PHASE-025, PHASE-029 | Discussion, post, and KB core CRUD built in parallel | Three content lanes merge independently (SLICE-010, 012, 014) |
| Sprint 5 | PHASE-021–024, PHASE-026–028, PHASE-030–032 | Moderation, drafts/comments, KB approval/revision | Content epics complete and verified (SLICE-011, 013, 015) |
| Sprint 6 | PHASE-033–036 | Search indexing, query API, reconciliation | Full-text search epic verified (SLICE-016–017) |
| Sprint 7 | PHASE-037–043 | Notifications, admin dashboard, rate limiting, CSRF hardening | Cross-cutting features complete (SLICE-018–020) |
| Sprint 8 | PHASE-044–046 | Accessibility, E2E, security/log/secrets audit | Ship gate passed (SLICE-021–022) |
| Sprint 9 | PHASE-047 | Documentation suite | Final documentation slice (SLICE-023) |

---

## Commit-Slice to Story Map

This table maps each commit slice to the stories it delivers and its merge boundary. It is the canonical traceability record linking stories → phases → slices → merge gates.

| Slice | Phase(s) | Story/Stories | Depends On | Merge Boundary |
|-------|----------|--------------|------------|----------------|
| SLICE-001 | PHASE-001, PHASE-002 | STORY-001, STORY-002 | None | Network + CI/CD gates verified in dev |
| SLICE-002 | PHASE-003, PHASE-004 | STORY-003, STORY-004 | SLICE-001 | WAF/edge headers pass VER-006/013 |
| SLICE-003 | PHASE-005 | STORY-005 | None (parallel) | Component library Storybook builds cleanly |
| SLICE-004 | PHASE-006, PHASE-007 | STORY-006, STORY-007 | SLICE-001 | Data-store connectivity + pipeline dry-run pass |
| SLICE-005 | PHASE-008, PHASE-009 | STORY-008, STORY-009 | SLICE-004 | Registration/verification tests green |
| SLICE-006 | PHASE-010, PHASE-011, PHASE-012 | STORY-010, STORY-011, STORY-012 | SLICE-005 | Login/MFA/reset/access-gating tests green |
| SLICE-007 | PHASE-013 | STORY-013 | SLICE-006 | Full auth/session suite passes — identity sign-off gate |
| SLICE-008 | PHASE-014, PHASE-015 | STORY-014, STORY-015 | SLICE-007 | Profile/avatar tests pass |
| SLICE-009 | PHASE-016, PHASE-017, PHASE-018, PHASE-019 | STORY-016–019 | SLICE-007 | Admin/taxonomy authorization suite passes — unblocks Sprint 4 |
| SLICE-010 | PHASE-020, PHASE-021 | STORY-020, STORY-021 | SLICE-009 | Thread/reply/lock/hide tests pass |
| SLICE-011 | PHASE-022, PHASE-023, PHASE-024 | STORY-022–024 | SLICE-010 | Moderation suite passes — completes discussion epic |
| SLICE-012 | PHASE-025, PHASE-026 | STORY-025, STORY-026 | SLICE-009 | Post/draft tests pass (parallel with SLICE-010) |
| SLICE-013 | PHASE-027, PHASE-028 | STORY-027, STORY-028 | SLICE-012 | Comment/publish-event tests pass — completes posts epic |
| SLICE-014 | PHASE-029, PHASE-030, PHASE-031 | STORY-029–031 | SLICE-009 | KB authoring/approval/revision tests pass (parallel with SLICE-010/012) |
| SLICE-015 | PHASE-032 | STORY-032 | SLICE-014 | KB suite passes — completes KB epic |
| SLICE-016 | PHASE-033, PHASE-035 | STORY-033, STORY-035 | SLICE-011, SLICE-013, SLICE-015 | Indexing + reconciliation tests pass (hard convergence: all 3 content types) |
| SLICE-017 | PHASE-034, PHASE-036 | STORY-034, STORY-036 | SLICE-016 | Search query/visibility suite passes — completes search epic |
| SLICE-018 | PHASE-037, PHASE-038, PHASE-039 | STORY-037–039 | SLICE-011, SLICE-013 | Notification dispatch suite passes |
| SLICE-019 | PHASE-040, PHASE-041 | STORY-040, STORY-041 | SLICE-011, SLICE-015 | Dashboard suite passes (parallel with SLICE-018) |
| SLICE-020 | PHASE-042, PHASE-043 | STORY-042, STORY-043 | SLICE-010, SLICE-012, SLICE-006 | Rate-limit/CSRF hardening tests pass (parallel with SLICE-018/019) |
| SLICE-021 | PHASE-044, PHASE-045 | STORY-044, STORY-045 | SLICE-017–020 | Accessibility + E2E gates green — ship-readiness gate |
| SLICE-022 | PHASE-046 | STORY-046 | SLICE-021 | Security/log/secrets audit clean — final hardening slice |
| SLICE-023 | PHASE-047 | STORY-047–051 | SLICE-022 | Docs reviewed — final documentation slice |

> **SLICE-016 is a hard convergence point.** It cannot merge until SLICE-011 (discussion), SLICE-013 (posts), and SLICE-015 (KB) are all in `main`. This enforces the design requirement that the search indexer handles all three content types correctly before the search query API is exposed.

> **SLICE-010 / SLICE-012 / SLICE-014 are intentionally independent.** Three developers can work them concurrently once SLICE-009 (taxonomy/roles) merges.

> **SLICE-018 / SLICE-019 / SLICE-020 may merge in any order** once their respective prerequisite slices are in `main`.

---

## Story-Level Requirements Traceability

Each story maps to one or more functional requirements defined in [Requirements](./requirements.md). The table below provides the cross-reference for audit and review purposes.

| Story | Functional Requirement(s) | Key AC IDs | VER IDs |
|-------|--------------------------|-----------|---------|
| STORY-001 | FR-12.1, FR-12.2 | — | VER-018 |
| STORY-002 | FR-12.3, FR-12.4 | — | VER-015, VER-018 |
| STORY-003 | FR-12.5 | — | VER-019 |
| STORY-004 | FR-12.6, FR-12.7, FR-12.8 | — | VER-006, VER-013 |
| STORY-008 | FR-01.8, FR-01.9 | — | VER-005–007 |
| STORY-009 | FR-01.1, FR-01.2 | AC-001.x, AC-002.x | VER-001, VER-012 |
| STORY-010 | FR-01.3, FR-01.4, FR-01.5 | AC-003.x, AC-004.x | VER-001, VER-016, VER-017 |
| STORY-011 | FR-01.6, FR-01.7 | AC-005.1, AC-005.2 | VER-008, VER-012 |
| STORY-012 | FR-01.10, FR-01.11 | AC-033.x | VER-004 |
| STORY-014 | FR-02.1 | AC-007.x | VER-004, VER-010 |
| STORY-015 | FR-02.2 | — | VER-021 |
| STORY-016 | FR-03.1, FR-03.2 | AC-008.1/.2/.4 | VER-004, VER-008 |
| STORY-017 | FR-03.3 | AC-032.1/.2 | VER-004 |
| STORY-018 | FR-04.1 | AC-028.2 | VER-004 |
| STORY-020 | FR-05.1 | AC-009.3 | VER-002, VER-010 |
| STORY-021 | FR-05.2, FR-05.3, FR-05.4 | AC-010.2, AC-012.3, AC-013.2/.3 | VER-002 |
| STORY-022 | FR-06.1 | AC-015.2 | VER-002 |
| STORY-023 | FR-06.2, FR-06.3 | AC-014.3/.4 | VER-002, VER-004 |
| STORY-025 | FR-07.1, FR-07.2 | AC-016.1/.3 | VER-002, VER-010 |
| STORY-026 | FR-07.3 | AC-017.1, AC-019.3 | VER-004 |
| STORY-027 | FR-07.4 | — | VER-002 |
| STORY-029 | FR-08.1 | AC-022.2/.3 | VER-002, VER-010 |
| STORY-030 | FR-08.2, FR-08.3 | AC-023.1/.2, AC-025.3 | VER-002, VER-004 |
| STORY-031 | FR-08.4 | AC-026.1/.2 | VER-002, VER-004 |
| STORY-033 | FR-09.1 | AC-027.5 | VER-003 |
| STORY-034 | FR-09.2 | AC-027.3/.4 | VER-003, VER-009 |
| STORY-035 | FR-09.3 | — | VER-003 |
| STORY-037 | FR-10.1 | — | VER-004 |
| STORY-038 | FR-10.2 | AC-029.2 | VER-024 |
| STORY-040 | FR-11.1 | AC-030.x | VER-004 |
| STORY-042 | NFR-04 (rate limit) | AC-031.2 | VER-020 |
| STORY-043 | NFR-004 (CSRF) | — | VER-013, VER-014 |
## Original Intent

Build a production-grade, AWS-native web platform that delivers identity and session management, user profiles, content publishing, full-text search, event-driven notifications, and an administration console — with security, observability, and operational excellence as first-class constraints. The platform must be deployable to two environments (beta and prod) via infrastructure-as-code and must adhere strictly to an AWS-only cloud guardrail.

---

## Requirements Summary

### Functional

- **FR-001 (Identity & Session):** Registration with email verification; login; MFA challenge/verify; failed-attempt lockout + owner alert; password reset with enumeration-safe response; session invalidation (all sessions) on reset; deny-by-default access gating with post-login redirect. (EPIC-002, TASK-015–024)
- **FR-002 (Profile):** Self-only `GET/PUT /api/v1/profile` with output encoding; pre-signed S3 avatar PUT/GET URL with content-type and size validation; private bucket with no public ACL. (EPIC-003, TASK-025–026)
- **FR-003 (Admin Account Management):** Admin activate/deactivate/delete with forced session invalidation; 403 for non-admin access. (EPIC-003, TASK-027–028)
- **FR-004 (Admin Role Assignment):** Moderator/Contributor role assign/revoke with per-request re-evaluation — role change effective without re-login. (EPIC-003, TASK-029)
- **FR-005 (Taxonomy):** Category/tag CRUD + archive (soft-state: archived category not selectable for new content but preserved on existing). (EPIC-003, TASK-030)
- **FR-006 (Discussion):** Thread create/list/filter/sort with sanitization; reply with lock-state rejection (423) and length validation; hide-state filtering (excluded from non-moderator views); non-author-edit 403; content-created EventBridge event on thread creation. (EPIC-004, TASK-032–035)
- **FR-007 (Moderation):** Report intake with duplicate-report unique constraint (409); moderator queue listing + lock/hide/delete actions; every action writes immutable audit record; 403 for non-moderator. (EPIC-004, TASK-036–037)
- **FR-008 (Posts):** Post create (draft/publish) with server-side sanitization; draft-only-visible-to-author/admin; edit/delete ownership enforcement; comment create; publish-state EventBridge event only on publish (not draft save). (EPIC-005, TASK-039–042)
- **FR-009 (Knowledge Base):** Contributor-only article create with sanitization (403 for non-Contributor); moderator/admin approve/reject with EventBridge event on approval; 404 for unapproved article on non-privileged direct URL access; append-only revision history restricted to author/moderator/admin. (EPIC-006, TASK-044–047)
- **FR-010 (Search):** Event-driven OpenSearch indexing (idempotent by entity_type/entity_id/version); hidden/unapproved content excluded; `GET /api/v1/search` with safe parameterized query and role-aware visibility filter; empty-state on no results; scheduled/manual full-reindex job (idempotent upsert). (EPIC-007, TASK-049–051)
- **FR-011 (Notifications):** Preference GET/PUT and notification list (self-only); SQS consumer/Lambda worker honoring opt-out; failed email falls back to in-portal only with no user-facing error. (EPIC-008, TASK-053–054)
- **FR-012 (Admin Dashboard):** Cross-content aggregation dashboard (accounts, content volume, moderation stats); admin-only access. (EPIC-009, TASK-056)
- **FR-013 (Infrastructure):** VPC/subnets/route tables (≥2 AZs); IAM roles (least-privilege, no long-lived keys); CI/CD SAST/SCA gates blocking critical/high findings; IaC plan-review gate for staging/prod applies; CloudWatch log groups + X-Ray; WAF with OWASP managed rules; API Gateway/ALB TLS 1.2+; Aurora KMS-encrypted (private-only); Redis replication group (multi-AZ, private-only). (EPIC-001, TASK-001–012)

### Non-Functional

- **NFR-003 (Cookie security):** Session cookie issued with `HttpOnly`, `Secure`, and `SameSite=Strict` attributes. (TASK-014)
- **NFR-004 (CSRF):** CSRF token middleware on all state-changing endpoints; requests without valid token rejected. (TASK-059, VER-014)
- **NFR-005 (Security headers):** CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options` present on all responses. (TASK-008, VER-013)
- **NFR-006 (AWS-only):** All runtime infrastructure in approved AWS accounts/regions. IAM roles for workload identity; no long-lived access keys.
- **NFR-008 (Encryption):** TLS 1.2+ in transit; AES-256 at rest for Aurora, S3, ElastiCache, OpenSearch.
- **NFR-009 (Logging hygiene):** Structured logs must not contain credentials, tokens, or PII beyond user ID. (TASK-063, VER-019)
- **NFR-010 (SCA gate):** CI pipeline blocks on critical/high SCA findings. (TASK-003, CON-004, VER-015)
- **NFR-016 (Correlation ID):** Structured JSON logs include a `correlationId` field on every request. (TASK-005, VER-019)
- **NFR-019 (Responsive):** No layout breakage at defined breakpoints (mobile/tablet/desktop). (TASK-061, VER-023)
- **NFR-WCAG (Accessibility):** WCAG 2.1 AA target; no critical/serious axe-core violations; manual audit sign-off. (TASK-060, VER-022)

---

## Plan Summary

| Phase | Goal | Key Deliverables | Tasks |
|-------|------|-----------------|-------|
| PHASE-001 | Network & Compute Foundation | VPC, subnets, security groups, IAM roles | TASK-001–002 |
| PHASE-002 | IaC Baseline & CI/CD Security Gates | CI pipeline with SAST/SCA + IaC plan-review gate | TASK-003–004 |
| PHASE-003 | Observability & WAF Edge | CloudWatch log groups, X-Ray, WAF with OWASP rules | TASK-005–006 |
| PHASE-004 | API Edge Gateway & Security Headers | TLS 1.2+, CSP/HSTS/X-Frame headers, CORS policy | TASK-007–008 |
| PHASE-005 | Shared Design-System | React component library: buttons, forms, pagination, states | TASK-009 |
| PHASE-006 | Baseline Data Stores | Aurora KMS-encrypted + ElastiCache Redis replication group | TASK-010–011 |
| PHASE-007 | Foundation Validation | Pipeline dry-run with vuln/secret test fixtures | TASK-012 |
| PHASE-008 | Session Store Integration | Redis-backed session create/read/expire/invalidate + secure cookie | TASK-013–014 |
| PHASE-009 | Registration & Email Verification | `POST /api/v1/auth/register`, SES verification token | TASK-015–016 |
| PHASE-010 | Login, MFA & Lockout | Login, lockout/delay + owner alert, MFA challenge/verify | TASK-017–019 |
| PHASE-011 | Password Reset & Session Invalidation | Enumeration-safe reset, all-session invalidation | TASK-020–021 |
| PHASE-012 | Access-Gating & Redirect Enforcement | Deny-by-default middleware, post-login redirect | TASK-022–023 |
| PHASE-013 | Identity & Session Validation | Full auth/session automated test suite in CI | TASK-024 |
| PHASE-014 | Member Profile Service | `GET/PUT /api/v1/profile` self-only, output-encoded | TASK-025 |
| PHASE-015 | Media/Asset Adapter | Pre-signed PUT/GET with content-type/size validation | TASK-026 |
| PHASE-016 | Admin Account Management | Account status endpoints + forced session invalidation | TASK-027–028 |
| PHASE-017 | Admin Role Assignment | Role assign/revoke with per-request re-evaluation | TASK-029 |
| PHASE-018 | Taxonomy Management | Category/tag CRUD + archive | TASK-030 |
| PHASE-019 | Profile/Admin/Taxonomy Validation | Authorization negative-test matrix across 5 roles | TASK-031 |
| PHASE-020 | Discussion Thread CRUD | Thread create/list/filter/sort + EventBridge event | TASK-032–033 |
| PHASE-021 | Discussion Reply, Lock & Hide State | Reply with lock-state rejection, hide-state filtering | TASK-034–035 |
| PHASE-022 | Moderation Report Intake | Report endpoint with duplicate-report constraint | TASK-036 |
| PHASE-023 | Moderation Review Queue & Actions | Queue listing + lock/hide/delete + audit trail | TASK-037 |
| PHASE-024 | Discussion & Moderation Validation | Full suite incl. rate-limit checks | TASK-038 |
| PHASE-025 | Post/Draft CRUD | Post create (draft/publish) with sanitization | TASK-039–040 |
| PHASE-026 | Draft Visibility & Ownership | Draft-only-visible filter, 404 on non-owner draft access | TASK-041 |
| PHASE-027 | Post Comments & Publish Events | Comment create + notification EventBridge event | TASK-042 |
| PHASE-028 | Post Validation Suite | Automated post-service test suite | TASK-043 |
| PHASE-029 | KB Article Authoring | Contributor-role-gated article create + sanitization | TASK-044 |
| PHASE-030 | KB Approval/Rejection Workflow | Approve/reject + visibility enforcement | TASK-045–046 |
| PHASE-031 | KB Revision History | Append-only revision on save, restricted access | TASK-047 |
| PHASE-032 | KB Validation Suite | Automated KB test suite | TASK-048 |
| PHASE-033 | Search Indexing Pipeline | Event consumer, idempotent upsert, STORE-007 mapping | TASK-049 |
| PHASE-034 | Search Query API | `GET /api/v1/search` with visibility filter + injection prevention | TASK-050 |
| PHASE-035 | Search Index Reconciliation Job | Scheduled/manual full-reindex job | TASK-051 |
| PHASE-036 | Search Validation Suite | Suite incl. injection and visibility-leakage tests | TASK-052 |
| PHASE-037 | Notification Preference API | Preference GET/PUT + notification list | TASK-053 |
| PHASE-038 | Notification Dispatch Worker | SQS consumer/Lambda honoring opt-out + SES fallback | TASK-054 |
| PHASE-039 | Notification Validation Suite | E2E scenario: reply → notification → opt-out suppression | TASK-055 |
| PHASE-040 | Admin Dashboard Aggregation | Dashboard aggregation queries (admin-only) | TASK-056 |
| PHASE-041 | Admin Dashboard Validation | Data accuracy + role restriction tests | TASK-057 |
| PHASE-042 | Fine-Grained Rate Limiting | Per-account/per-window limits on reg/login/content | TASK-058 |
| PHASE-043 | CSRF & Security Headers Hardening | CSRF middleware on all state-changing endpoints | TASK-059 |
| PHASE-044 | Accessibility & Responsive Verification | axe-core scan + manual audit + cross-viewport tests | TASK-060–061 |
| PHASE-045 | E2E Critical Journey Verification | JRN-001–009 happy-path + key alternates | TASK-062 |
| PHASE-046 | Security, Log & Secrets Compliance Audit | Log PII review + IaC hardcoded-secret scan | TASK-063–064 |
| PHASE-047 | Documentation Suite | README, architecture, getting-started, decision log, contributing guide | TASK-065–069 |

> Full plan detail: [plan.md](./plan.md)

---

## Design Decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| **Compute** | ECS/Fargate (pending DEC-005 final lock-in) | Serverless containers reduce operational overhead vs EC2; avoids Kubernetes complexity for this scale |
| **Database** | Aurora PostgreSQL (Serverless v2 / Provisioned) | Multi-AZ HA, PostgreSQL compatibility, familiar relational model; DynamoDB considered but relational integrity required |
| **Cache / Sessions** | ElastiCache Redis (`STORE-002`) | Token blacklist needs atomic set operations; Redis TTL semantics fit JWT revocation and rate-limit counters; ElastiCache is fully managed |
| **Async messaging** | EventBridge + SQS (`IF-017`) | EventBridge for schema-aware event routing + replay; SQS for per-consumer durable queues with DLQ; decouples API write path from search indexing and notification dispatch |
| **Email / in-portal notifications** | AWS SES (email) + in-portal fallback (COMP-008) | SES is the confirmed MVP channel; in-portal is the graceful fallback on SES failure (AC-029.2); SNS Push / SMS deferred to DEC-002 |
| **IaC** | OpenTofu with per-environment var-files | Open-source Terraform-compatible; per-env `beta.tfvars` / `prod.tfvars` for clean environment separation; AWS-provider-only |
| **Secrets** | AWS Secrets Manager | Rotation support, CloudTrail audit, fine-grained IAM; injected into ECS tasks at launch — never baked into images |
| **Session cookie** | `HttpOnly; Secure; SameSite=Strict` (TASK-014) | Mitigates XSS-based token theft and CSRF; satisfies NFR-003 |
| **Role evaluation model** | Per-request DB re-evaluation for privilege-sensitive operations (TASK-029) | Ensures moderator/admin role changes are effective immediately without re-login (AC-032.1/.2); avoids stale-claim vulnerability from long-lived role-in-JWT designs |
| **WAF** | AWS WAF in front of ALB (`infra/waf/`) | OWASP managed rule group, rate limiting, bot control — reduces OWASP Top 10 surface at the edge without application code changes; TASK-006 |
| **Observability** | CloudWatch + X-Ray (`infra/observability/`) | AWS-native; structured JSON logs with `correlationId`; X-Ray trace propagation across ECS tasks; no third-party SaaS required (NFR-016) |
| **Search indexing idempotency** | Idempotent upsert keyed on `(entity_type, entity_id, version)` | Handles SQS redelivery without duplication; safe for full-reindex reconciliation (TASK-049/051) |
| **KB approval workflow** | Moderator/admin approve/reject before content becomes visible | Prevents unapproved KB articles from leaking into search index or member views (AC-023.1/.2, AC-025.3); EventBridge event on approval triggers indexing |
| **Moderation audit trail** | Append-only Aurora `audit_log` table + structured CloudWatch log | Satisfies AC-014.3/.4 (immutable per-action record) and NFR-016 (structured correlation log) |
| **Draft visibility** | 404 (not 403) on non-owner draft access | Avoids content-existence enumeration; satisfies AC-017.1, AC-019.3 (TASK-041) |
| **Report deduplication** | Unique constraint on `(reporter_id, target_id)` → 409 | Prevents spam reporting; satisfies AC-015.2 (TASK-036) |
| **CSRF protection** | CSRF token middleware on all state-changing endpoints (`services/*/middleware/csrf.*`) | Mitigates CSRF attacks on session-cookie-based auth (NFR-004, VER-014, TASK-059) |
| **Rate limiting** | Per-account/per-window limits in Redis, layered under edge WAF throttling | Dual-layer defense: WAF handles broad IP-level throttling; Redis handles per-account abuse (TASK-058, AC-031.2, VER-020) |

### Open Decisions (blocking production lock-in)

| ID | Topic | Blocked Stories | Expected Resolution |
|----|-------|-----------------|---------------------|
| DEC-001 | Server-side content sanitiser library selection | TASK-032 (threads), TASK-039 (posts), TASK-044 (KB) | Before PHASE-020 ships to prod |
| DEC-002 | Notification channel scope (SMS / Push beyond SES + in-portal) | TASK-054 (notification dispatch) | Before PHASE-038 ships to prod |
| DEC-003 | Sanitiser HTML whitelist configuration | Same as DEC-001 | Before PHASE-020 ships to prod |
| DEC-005 | Compute platform final lock-in (ECS vs EKS vs App Runner) | TASK-001 (VPC/network), TASK-010 (Aurora) | Before PHASE-001 prod apply |
| DEC-006 | OpenSearch cluster sizing and node type | TASK-049 (search indexer) | Before PHASE-033 prod apply |

> See [Design](./design.md) §16–17 for full open-decision records and owners.

---

## Security Notes

- Authentication (Identity epic, PHASE-008–013) completes before any Profile, Admin, Content, or Search API surface is exposed (PHASE-014+) — satisfying the "auth precedes exposure" guardrail rule.
- All OWASP Top 10 categories are addressed: WAF OWASP managed rules (A01/A05, TASK-006); JWT + Redis revocation + per-request role re-evaluation (A07, TASK-017/029); parameterised queries / ORM (A03, TASK-032/039/044/050); Secrets Manager (A02/A09); structured logging without sensitive data (A09, TASK-063, VER-019); SCA/SAST gates in CI (A06/A08, TASK-003, VER-015); server-side input validation + sanitisation (A03/A04, pending DEC-001/DEC-003); SSRF egress restricted to known AWS endpoints via security group (A10); CSRF middleware on all state-changing endpoints (NFR-004, TASK-059, VER-014).
- Dedicated PHASE-046 security/log/secrets compliance audit (TASK-063–064) runs after all feature phases and E2E suite before documentation phase.

---

## Verification Evidence Map

Cross-reference between VER IDs (design §verification) and the tasks that satisfy them:

| VER ID | What It Verifies | Satisfying Task(s) |
|--------|------------------|--------------------|
| VER-001 | Registration + login + verification flows | TASK-015, TASK-016, TASK-017 |
| VER-002 | Content CRUD, lock/hide, moderation, posts, KB | TASK-032–037, TASK-039–047 |
| VER-003 | Search query correctness + injection safety | TASK-050, TASK-052 |
| VER-004 | Authorization — all roles, negative tests | TASK-022, TASK-025, TASK-027–031, TASK-035, TASK-037 |
| VER-005–008 | Session create/read/expire/invalidate + cookie attributes | TASK-013, TASK-014, TASK-021 |
| VER-009 | Search empty-state + no-results handling | TASK-050 |
| VER-010 | Output encoding on free-text fields | TASK-025, TASK-032, TASK-039, TASK-044 |
| VER-012 | Enumeration safety (registration 409, reset identical response) | TASK-015, TASK-020 |
| VER-013 | Security headers on all responses | TASK-008 (CI gate) |
| VER-014 | CSRF token rejection on state-changing endpoints | TASK-059 |
| VER-015 | CI pipeline blocks on intentional vulnerable dependency | TASK-003, TASK-012 |
| VER-016 | MFA invalid/expired factor rejected + logged | TASK-019 |
| VER-017 | Lockout/delay + owner alert at threshold | TASK-018 |
| VER-018 | No hardcoded secrets + only approved AWS resources in IaC | TASK-012, TASK-064 |
| VER-019 | Structured logs with correlationId; no PII/secrets in logs | TASK-005, TASK-063 |
| VER-020 | Rate-limit 429 generic message on threshold breach | TASK-038, TASK-043, TASK-058 |
| VER-021 | Pre-signed S3 URL private bucket, time-limited, no public ACL | TASK-026 |
| VER-022 | No critical/serious axe-core violations | TASK-060 |
| VER-023 | No layout breakage at defined breakpoints | TASK-061 |
| VER-024 | JRN-001–009 happy-path + key alternates E2E | TASK-062 |
