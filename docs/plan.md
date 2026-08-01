# Generated Plan

> This document preserves the generated delivery plan, updated to include the Phase 3 phase/task breakdown. See [Requirements](./requirements.md) for what is being built, [Design](./design.md) for how it is built, and [Decision Log](./decision-log.md) for why key choices were made.

---

| Total Stories / Tasks | 51 stories / 69 implementation tasks |
| Total Story Points | 253 (11 epics) |
| Parallel Stories (max in one sprint) | 4 (Sprint 1, Lanes A–D) |
| Critical Path Phases | PHASE-001 → PHASE-013 → PHASE-019 → PHASE-024 → PHASE-028 → PHASE-032 → PHASE-036 → PHASE-046 → PHASE-047 |
| Optimized Duration (2 devs, full parallelism) | 11 sprints (22 weeks) |
| Estimated Ship Date | Week 22 from start |

---

## Epic Summary (Phase 3 Model)

| Epic | Name | Story Points | Critical Path | Phases |
|------|------|-------------|---------------|--------|
| EPIC-001 | AWS Foundation & IaC Baseline | 34 | Yes | PHASE-001–007 |
| EPIC-002 | Identity & Session | 34 | Yes | PHASE-008–013 |
| EPIC-003 | Profile, Admin & Taxonomy | 33 | Yes | PHASE-014–019 |
| EPIC-004 | Discussion & Moderation | 26 | Yes | PHASE-020–024 |
| EPIC-005 | Posts | 21 | Yes | PHASE-025–028 |
| EPIC-006 | Knowledge Base | 23 | Yes | PHASE-029–032 |
| EPIC-007 | Search | 21 | Yes | PHASE-033–036 |
| EPIC-008 | Notifications | 16 | No (parallel) | PHASE-037–039 |
| EPIC-009 | Admin Dashboard | 8 | No (parallel) | PHASE-040–041 |
| EPIC-010 | Cross-Cutting Security, Observability & Accessibility | 26 | Partial (PHASE-045 ship-blocking) | PHASE-042–046 |
| EPIC-011 | Documentation | 11 | No (required before ship) | PHASE-047 |
---

## Phase-by-Phase Task Breakdown

### PHASE-001: Network & Compute Foundation
**Objective:** Provision the AWS network/compute base for all workloads.

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-001 | Backend | `infra/network/*.tf` | VPC + subnets (≥2 AZs) clean `terraform plan/apply` |
| TASK-002 | Backend | `infra/iam/*.tf` | ECS/Lambda roles scoped per module; no static access keys |

### PHASE-002: IaC Baseline & CI/CD Security Gates
**Objective:** CI pipeline with SAST/SCA gates + IaC plan-review workflow.

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-003 | Backend | `.github/workflows/*.yml` | Pipeline fails on critical/high CVE (VER-015) |
| TASK-004 | Backend | `infra/ci/*` | No apply without reviewed plan artifact |

### PHASE-003: Observability & WAF Edge Setup

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-005 | Backend | `infra/observability/*.tf` | Structured JSON logs + correlation ID + X-Ray (NFR-016, VER-019) |
| TASK-006 | Backend | `infra/waf/*.tf` | WAF blocks OWASP managed rule matches |

### PHASE-004: API Edge Gateway & Security Headers

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-007 | Backend | `infra/edge/*.tf` | TLS 1.2+ only; HTTP → HTTPS redirect (VER-006) |
| TASK-008 | Backend | `edge/middleware/headers.*` | CSP, HSTS, X-Frame-Options, X-Content-Type-Options (NFR-005, VER-013) |

### PHASE-005: Shared Design-System Component Library

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-009 | Frontend | `web/src/components/*`, `web/src/design-system/*` | Storybook renders button/form/list/pagination/empty/error/permission-denied; axe-core baseline |

### PHASE-006: Baseline Data Stores

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-010 | Backend | `infra/data/aurora.tf` | Private-only, KMS-encrypted, automated backups enabled (VER-006) |
| TASK-011 | Backend | `infra/data/elasticache.tf` | Redis private-only; multi-AZ replication enabled |

### PHASE-007: Foundation Validation

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-012 | Testing | CI pipeline test fixtures | Pipeline blocks intentional vuln dep + hardcoded secret (VER-015, VER-018) |

### PHASE-008: Session Store Integration

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-013 | Backend | `services/identity/session-store.*` | TTL honored; explicit invalidation deletes key immediately (VER-007 prep) |
| TASK-014 | Backend | `services/identity/cookie.*` | `HttpOnly; Secure; SameSite=Strict` cookie (NFR-003, VER-007) |

### PHASE-009: Registration & Email Verification

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-015 | Backend | `services/identity/register.*`, `STORE-001` migration | Generic 409 on conflict; 400 on policy violation; input sanitized (AC-001.x, VER-001, VER-012) |
| TASK-016 | Backend | `services/identity/verify.*`, SQS queue, SES template | Single-use time-limited token; 410 on expired/used; resend available (AC-002.x, VER-001) |

### PHASE-010: Login, MFA & Lockout

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-017 | Backend | `services/identity/login.*` | Generic 401; account-status check (AC-003.x, VER-001) |
| TASK-018 | Backend | `services/identity/lockout.*` | Lockout/delay at threshold; owner alert emitted (AC-004.x, VER-017) |
| TASK-019 | Backend | `services/identity/mfa.*` | Invalid/expired factor rejected and logged (VER-016) |

### PHASE-011: Password Reset & Session Invalidation

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-020 | Backend | `services/identity/reset.*` | Identical response regardless of email existence (AC-005.1, VER-012) |
| TASK-021 | Backend | `services/identity/reset.*`, `session-store.*` | All existing sessions invalidated (AC-005.2, VER-008) |

### PHASE-012: Access-Gating & Redirect Enforcement

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-022 | Backend | `services/*/middleware/authn.*` | Unauthenticated → redirect/401 to `/login` (AC-033.x, VER-004) |
| TASK-023 | Frontend | `web/src/routing/guards.*` | Post-login redirect to original URL (AC-033.2) |

### PHASE-013: Identity & Session Validation Suite

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-024 | Testing | `tests/identity/*` | VER-001, VER-005–008, VER-012, VER-016, VER-017 all pass |

### PHASE-014: Member Profile Service

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-025 | Backend | `services/profile/*` | 403 on cross-user; free-text output-encoded (AC-007.x, VER-004, VER-010) |

### PHASE-015: Media/Asset Adapter

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-026 | Backend | `services/media/*`, S3 bucket policy | Private bucket; no public ACL; time-limited pre-signed URL (VER-021) |

### PHASE-016: Admin Account Management

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-027 | Backend | `services/admin/accounts.*` | Deactivation invalidates all sessions immediately (AC-008.1/.2, VER-004, VER-008) |
| TASK-028 | Backend | `services/admin/middleware/authz.*` | 403 for non-admin (AC-008.4, VER-004) |

### PHASE-017: Admin Role Assignment

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-029 | Backend | `services/admin/roles.*` | Role effective without re-login (AC-032.1/.2, VER-004) |

### PHASE-018: Taxonomy Management

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-030 | Backend | `services/admin/taxonomy.*`, `STORE-009` | Archived category not selectable; preserved on existing (AC-028.2, VER-004) |

### PHASE-019–046: Feature & Validation Phases

See [Decision Log](./decision-log.md) Plan Summary table for PHASE-019 through PHASE-046 task details. The discussion, posts, KB, search, notifications, admin dashboard, rate limiting, CSRF hardening, accessibility, E2E, and security audit phases all follow the same pattern: implement → test suite → validation evidence captured in CI.

### PHASE-047: Documentation Suite

| Task | Type | Files | AC Summary |
|------|------|-------|-----------|
| TASK-065 | Documentation | `README.md`, `docs/README.md` | New engineer can clone and run locally using README alone |
| TASK-066 | Documentation | `docs/architecture.md` | Matches COMP-001–012 model from design Section 3 |
| TASK-067 | Documentation | `docs/getting-started.md` | All env vars and commands used in CI documented |
| TASK-068 | Documentation | `docs/decision-log.md` | Captures DSN-001–009, DEC-001–006 status |
| TASK-069 | Documentation | `CONTRIBUTING.md` | Branch naming, PR review, lint/test requirements documented |

## Project Summary

| Metric | Value |
|--------|-------|
| Total Epics | 11 |

---

## Guardrail Compliance

| Guardrail | Status | Notes |
|-----------|--------|-------|
| Security / Auth | ✅ Pass | Identity & Session epic (STORY-008–013) completes in Sprint 2, fully ahead of any Profile/Admin/Content/Search API exposure starting Sprint 3 — satisfies "auth precedes exposure" rule |
| Testing Coverage | ✅ Pass | Every feature epic carries a dedicated validation story in the same or immediately following sprint (STORY-007, 013, 019, 024, 028, 032, 036, 039, 041) plus cross-cutting E2E/security/accessibility gates in Sprint 8 |
| Dependency Integrity | ✅ Pass | No circular dependencies detected. COMP-001 (Identity) is the dependency root; COMP-006/007/008 are one-way downstream consumers, matching design Section 3 |
| AWS-only | ✅ Pass | All infra/runtime stories (STORY-001–006, 033, 038) use only AWS-native services (VPC, ECS/Fargate, Aurora, ElastiCache, S3, SES, OpenSearch, EventBridge/SQS, CloudWatch, X-Ray, WAF, IAM) |
| Decision Readiness | ⚠️ WARNING (informational) | STORY-001 (compute platform), STORY-033 (search engine/sizing), STORY-038 (notification channel scope), and STORY-020/025/029 (sanitiser) are blocked on DEC-005/DEC-006/DEC-002/DEC-003/DEC-001 for final lock-in. Architecture/interface work may proceed; production provisioning/library lock-in must wait for decision confirmation |

---

## Epics

| Epic | Name | Sprint(s) | Stories |
|------|------|-----------|---------|
| EPIC-01 | Infrastructure Foundation | 1 | STORY-001–007 |
| EPIC-02 | Identity & Sessions | 2 | STORY-008–013 |
| EPIC-03 | User Profiles | 3 | STORY-014–019 |
| EPIC-04 | Content — Core Authoring | 4 | STORY-020–021, 025–026, 029 |
| EPIC-05 | Content — Advanced | 5 | STORY-022–024, 027–028, 030–032 |
| EPIC-06 | Search | 6 | STORY-033–036 |
| EPIC-07 | Notifications | 7 | STORY-037–039 |
| EPIC-08 | Administration | 7 | STORY-040–043 |
| EPIC-09 | Quality Gates | 8 | STORY-044–046 |
| EPIC-10 | Hardening & Performance | 9 | STORY-047–050 |
| EPIC-11 | Production Readiness & Launch | 9 | STORY-051 |

---

## Sprint-by-Sprint Breakdown

### Sprint 1 — Infrastructure Foundation

**Goal:** Provision the complete AWS infrastructure baseline so all subsequent sprints have a running environment to deploy into.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-001, STORY-006 | ECS/Fargate cluster + CloudWatch/X-Ray observability baseline |
| B | STORY-002, STORY-007 | Aurora PostgreSQL cluster + observability integration tests |
| C | STORY-003, STORY-004 | VPC + networking, ElastiCache Redis |
| D | STORY-005 | S3 buckets, ECR repositories, WAF Web ACL |

**Key deliverables:**
- VPC with public/private subnets, NAT Gateway, Internet Gateway
- ECS Fargate cluster with auto-scaling policies
- Aurora PostgreSQL (Serverless v2) — multi-AZ in prod
- ElastiCache Redis cluster
- S3 buckets (assets, logs, backups)
- ECR repositories (api, worker, admin)
- AWS WAF Web ACL attached to ALB
- CloudWatch log groups, dashboards, and baseline alarms
- X-Ray sampling rules and service map

**Acceptance:** IaC applies cleanly to beta. ECS service healthy. CloudWatch dashboards rendering. WAF active. All STORY-007 validation tests pass.

**Open decision gate:** DEC-005 (compute platform) must be confirmed before final prod provisioning.

---

### Sprint 2 — Identity & Sessions

**Goal:** Deliver a complete, tested authentication and session management system that gates all subsequent API surfaces.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-008, STORY-010, STORY-012 | Registration + email verification; JWT issuance + refresh; password recovery |
| B | STORY-009, STORY-011, STORY-013 | Login + session store (Redis); token revocation + MFA groundwork; auth test suite |

**Key deliverables:**
- Registration endpoint with email verification flow (SES)
- Login endpoint returning JWT access + refresh token pair
- Redis-backed session store for refresh tokens
- Token refresh endpoint
- Bulk and per-session token revocation
- MFA data model and interface (enforcement policy deferred)
- Password recovery via time-limited email link (SES)
- Full automated test suite (unit + integration) covering all auth flows

**Acceptance:** All STORY-013 test cases pass. No unauthenticated access to any protected route.

---

### Sprint 3 — User Profiles

**Goal:** Deliver profile management and avatar upload behind the authentication layer established in Sprint 2.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-014, STORY-015 | Profile CRUD API; visibility settings |
| B | STORY-016, STORY-017 | Avatar upload (S3 integration); MIME-type and size validation |
| C | STORY-018, STORY-019 | Profile search/list (admin); profile test suite |

**Key deliverables:**
- Profile create/read/update/delete endpoints
- Avatar upload to S3 with MIME-type validation
- Visibility settings (public, private, followers-only — TBD on granularity)
- Admin read-any-profile capability
- Full test suite (STORY-019)

**Acceptance:** Users cannot read or modify other users' private profiles. Avatar upload rejects non-image types. STORY-019 tests pass.

---

### Sprint 4 — Content Authoring (Core)

**Goal:** Deliver the foundational content creation, sanitisation, and media-attachment capabilities.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-020, STORY-021 | Content create/edit/delete API; content state machine (draft → published → archived → flagged) |
| B | STORY-025, STORY-026 | Media upload for content (S3); media list and delete |
| C | STORY-029 | Server-side content sanitisation integration (pending DEC-001/DEC-003) |

**Open decision gate:** DEC-001 (sanitiser library) and DEC-003 (whitelist config) must be resolved before STORY-020/025/029 can be completed in production.

**Key deliverables:**
- Content CRUD endpoints
- Content state machine
- Media upload/list/delete endpoints
- Server-side sanitiser integrated at API boundary

---

### Sprint 5 — Content Authoring (Advanced)

**Goal:** Add versioning, revision history, and list/filter capabilities; complete content test coverage.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-022, STORY-023, STORY-024 | Content versioning; revision history retrieval; content test suite |
| B | STORY-027, STORY-028 | Moderation queue; moderation test suite |
| C | STORY-030, STORY-031, STORY-032 | Content list/filter/pagination; content search integration hooks; list test suite |

**Key deliverables:**
- Immutable revision records per content update
- Revision history retrieval endpoint
- Moderation queue (list flagged items, approve/reject)
- Paginated, filtered content list endpoint
- Full test suites (STORY-024, 028, 032)

---

### Sprint 6 — Search

**Goal:** Provision OpenSearch, build the indexing pipeline, and expose the search API.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-033, STORY-035 | OpenSearch provisioning (IaC, pending DEC-006); search API endpoint |
| B | STORY-034, STORY-036 | Indexing worker (EventBridge → Worker → OpenSearch); search test suite |

**Open decision gate:** DEC-006 (OpenSearch cluster sizing) must be confirmed before production provisioning.

**Key deliverables:**
- OpenSearch domain provisioned in IaC
- EventBridge → SQS → Worker → OpenSearch indexing pipeline
- Search API with keyword, relevance, and facet support
- Test suite (STORY-036)

---

### Sprint 7 — Notifications & Administration

**Goal:** Deliver notification dispatch and the admin console in parallel.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-037, STORY-038, STORY-039 | Notification preferences API; notification dispatch worker (SES + pending DEC-002); notification test suite |
| B | STORY-040, STORY-041 | Admin user/role management; admin test suite |
| C | STORY-042, STORY-043 | Admin content moderation console; audit log |

**Open decision gate:** DEC-002 (notification channel scope) must be confirmed before STORY-038 production provisioning.

**Key deliverables:**
- Notification preference model and API
- Worker SES dispatch integration
- Admin role management endpoints
- Admin content moderation console
- Append-only audit log
- Test suites (STORY-039, 041)

---

### Sprint 8 — Quality Gates

**Goal:** Comprehensive cross-cutting test coverage before production readiness.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-044 | End-to-end test suite (full user journey, deployed beta) |
| B | STORY-045 | Security test suite (auth bypass, injection, SSRF, OWASP checks) |
| C | STORY-046 | Accessibility test suite (WCAG 2.1 AA baseline) |

**Acceptance:** All three test suites pass in the beta environment before Sprint 9 begins.

---

### Sprint 9 — Hardening & Production Launch

**Goal:** Performance tuning, documentation, runbook, and production launch.

| Lane | Stories | Description |
|------|---------|-------------|
| A | STORY-047, STORY-048 | Load and performance testing; performance tuning |
| B | STORY-049, STORY-050 | Runbook and operational documentation; dependency/SBOM audit |
| C | STORY-051 | Production readiness review + launch |

**Key deliverables:**
- Load test results and tuning applied
- Operational runbook (incident response, scaling, backup/restore)
- SBOM and vulnerability scan report
- Production readiness checklist completed
- Prod environment deployed and smoke-tested

---

## Dependency Graph (summary)

```
EPIC-01 (Infra) ──► EPIC-02 (Identity) ──► EPIC-03 (Profiles)
                                        ──► EPIC-04/05 (Content)
                                        ──► EPIC-06 (Search)
                                        ──► EPIC-07 (Notifications)
                                        ──► EPIC-08 (Admin)
EPIC-09 (Quality Gates) ──► EPIC-10/11 (Hardening / Launch)
```

No circular dependencies. COMP-001 (Identity) is the dependency root for all feature epics.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| DEC-005 compute platform decision delayed | Medium | High (blocks Sprint 1 prod apply) | Architecture/interface work can proceed; gate prod provisioning on decision |
| DEC-001/DEC-003 sanitiser decision delayed | Medium | Medium (blocks Sprint 4 completion) | Sanitiser interface can be stubbed; content persist blocked until approved library confirmed |
| DEC-006 OpenSearch sizing under-provisioned | Low | Medium (search latency at load) | Load test in Sprint 9 will validate; right-sizing can be applied via IaC |
| SES production send limits not raised before Sprint 2 | Medium | High (breaks auth email flow) | Raise SES limits as a Sprint 1 prerequisite action item |
| Sprint 7 parallelism (3 lanes, 2 devs) extends timeline | Medium | Low (1–2 day slip) | Accept; Sprints 7 is flagged in the execution map as extended with 2 developers |

---

## Success Criteria

- All 51 stories completed and accepted.
- All guardrail checks pass (security, testing, dependency integrity, AWS-only).
- All open decisions (DEC-001–DEC-006) resolved before their respective production gate.
- Sprint 8 quality gates (E2E, security, accessibility) pass in beta.
- Sprint 9 production readiness review approved.
- Production environment deployed, smoke-tested, and handed to operations.
