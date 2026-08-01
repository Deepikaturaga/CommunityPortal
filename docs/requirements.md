# Generated Requirements

> This document preserves the requirements as generated during the planning phase, updated to reflect the detailed acceptance criteria established in Phase 3 task definitions. See [Decision Log](./decision-log.md) for the original intent and design trade-offs, and [Plan](./plan.md) for delivery sequencing.

---

- **FR-01.1** `POST /api/v1/auth/register` validates uniqueness and password policy; returns generic 409 on conflict (no field disclosure); input is sanitized before persistence. (AC-001.x, TASK-015)
- **FR-01.2** Email verification issues a single-use, time-limited token via SES; returns 410 on expired/used token; resend offer is available. (AC-002.x, TASK-016)
- **FR-01.3** `POST /api/v1/auth/login` returns generic 401 on bad credential or deactivated account — no enumeration signal. (AC-003.x, TASK-017)
- **FR-01.4** Failed-attempt lockout/delay triggers at threshold; owner alert is emitted. (AC-004.x, TASK-018)
- **FR-01.5** MFA challenge/verify endpoint rejects invalid/expired factors and logs the event. (TASK-019)
- **FR-01.6** Password reset request returns identical response regardless of email existence (enumeration-safe). (AC-005.1, TASK-020)
- **FR-01.7** Password reset completion invalidates all existing sessions for the account immediately. (AC-005.2, TASK-021)
- **FR-01.8** Session store client supports create, read, expire, and invalidate operations; TTL is honored; explicit invalidation deletes the Redis key immediately. (TASK-013)
- **FR-01.9** Session cookie is issued with `HttpOnly`, `Secure`, and `SameSite=Strict` attributes. (NFR-003, TASK-014)
- **FR-01.10** Every protected route enforces deny-by-default auth middleware; unauthenticated requests are redirected/401 to `/login`. (AC-033.x, TASK-022)
- **FR-01.11** Post-login redirect restores the original pre-login URL. (AC-033.2, TASK-023)
- **FR-02.1** `GET/PUT /api/v1/profile` is self-only; cross-user access returns 403; free-text fields are output-encoded. (AC-007.x, TASK-025)
- **FR-02.2** Media/asset adapter issues pre-signed S3 PUT/GET URLs with content-type and size validation; the bucket is private with no public ACL; URLs are time-limited. (TASK-026, VER-021)

### FR-03 — Admin Account & Role Management
- **FR-03.1** Admin account status endpoints (activate/deactivate/delete) immediately invalidate all sessions for the affected account. (AC-008.1/.2, TASK-027)
- **FR-03.2** Non-admin access to admin endpoints returns 403. (AC-008.4, TASK-028)
- **FR-03.3** Role assign/revoke uses per-request re-evaluation — role change is effective without re-login. (AC-032.1/.2, TASK-029)

### FR-04 — Taxonomy
- **FR-04.1** Category/tag CRUD supports archive (soft-state); archived category is not selectable for new content but preserves the label on existing content. (AC-028.2, TASK-030)

_(Superseded by the more granular FR-05–FR-09 below; legacy FR-03 items retained for traceability.)_

### FR-05 — Discussion
- **FR-05.1** Thread create/list/filter/sort endpoints validate non-empty body, sanitize content pre-storage, and emit a `IF-017` content-created EventBridge event. (AC-009.3, TASK-032–033)
- **FR-05.2** Reply to a locked thread returns 423. (AC-010.2, TASK-034)
- **FR-05.3** Hidden content is excluded from non-moderator views. (AC-012.3, TASK-035)
- **FR-05.4** Non-author edit attempt returns 403. (AC-013.2/.3, TASK-035)

### FR-06 — Moderation
- **FR-06.1** Report endpoint enforces a unique constraint on `(reporter_id, target_id)`; returns 409 on duplicate. (AC-015.2, TASK-036)
- **FR-06.2** Moderator queue listing + lock/hide/delete actions command COMP-003; every action writes an immutable audit record. (AC-014.3/.4, TASK-037)
- **FR-06.3** Non-moderator access to moderation endpoints returns 403. (TASK-037)

### FR-07 — Posts
- **FR-07.1** Post create (draft/publish) applies server-side sanitization. (AC-016.1/.3, TASK-039)
- **FR-07.2** `IF-017` event fires only on publish state transition, not on draft save. (TASK-040)
- **FR-07.3** Draft posts are visible only to author and admin; non-owner draft access returns 404. (AC-017.1, AC-019.3, TASK-041)
- **FR-07.4** Comment create endpoint emits a `IF-017` event for downstream notification consumers. (TASK-042)

### FR-08 — Knowledge Base
- **FR-08.1** Article create endpoint enforces Contributor role; returns 403 for non-Contributors; content is sanitized pre-storage. (AC-022.2/.3, TASK-044)
- **FR-08.2** Approve/reject endpoints: approve makes the article visible to all members and emits an EventBridge index event; reject returns the article to draft with a note. (AC-023.1/.2, TASK-045)
- **FR-08.3** Non-privileged direct URL access to unapproved article returns 404. (AC-025.3, TASK-046)
- **FR-08.4** Revision-on-save is append-only; revision history is restricted to author/moderator/admin. (AC-026.1/.2, TASK-047)

### FR-09 — Full-Text Search
- **FR-09.1** Event consumer indexes create/update/delete/approve/hide events idempotently by `(entity_type, entity_id, version)`; hidden/unapproved content is excluded from the index. (AC-027.5, TASK-049)
- **FR-09.2** `GET /api/v1/search` uses safe parameterized queries and a role-aware visibility filter; returns empty-state on no results. (AC-027.3/.4, TASK-050)
- **FR-09.3** Scheduled/manual full-reindex job produces an identical index state on re-run (idempotent upsert). (TASK-051)

### FR-10 — Notifications
- **FR-10.1** Notification preference GET/PUT and notification list endpoint enforce self-only access; opt-out flags are persisted. (TASK-053)
- **FR-10.2** SQS consumer/Lambda worker maps `IF-017` events to notifications, honoring opt-out; failed SES delivery falls back to in-portal only with no user-facing error. (AC-029.2, TASK-054)

### FR-11 — Admin Dashboard
- **FR-11.1** Dashboard aggregation queries (accounts, content volume, moderation stats) are admin-only; aggregate figures match source data. (AC-030.x, TASK-056)

### FR-12 — Infrastructure
- **FR-12.1** VPC with public/private subnets across ≥2 AZs applies cleanly via `terraform plan/apply`. (TASK-001)
- **FR-12.2** ECS task roles and Lambda execution roles are scoped per module; no static access keys. (TASK-002)
- **FR-12.3** CI pipeline fails on critical/high vulnerability findings (SAST/SCA). (TASK-003, CON-004, NFR-010)
- **FR-12.4** No IaC apply proceeds without a reviewed plan artifact for staging/prod. (TASK-004)
- **FR-12.5** Structured JSON logs with `correlationId` and X-Ray traces are active from first deploy. (TASK-005, NFR-016)
- **FR-12.6** WAF blocks common attack signatures (OWASP managed rules). (TASK-006)
- **FR-12.7** TLS 1.2+ enforced; HTTP redirects to HTTPS. (TASK-007, VER-006)
- **FR-12.8** CSP, HSTS, `X-Frame-Options`, and `X-Content-Type-Options` are present on all responses. (TASK-008, NFR-005)
- **FR-12.9** Aurora cluster: private-only, KMS-encrypted at rest, automated backups enabled. (TASK-010)
- **FR-12.10** Redis replication group: reachable only from app subnet, multi-AZ replication enabled. (TASK-011)

---

## Acceptance Criteria — Key AC IDs

| AC ID | Description | Satisfying Task |
|-------|-------------|----------------|
| AC-001.x | Registration uniqueness, password policy, generic 409 | TASK-015 |
| AC-002.x | Single-use, time-limited email verification; 410 on expired | TASK-016 |
| AC-003.x | Generic 401 on bad credential / deactivated account | TASK-017 |
| AC-004.x | Lockout at threshold + owner alert | TASK-018 |
| AC-005.1 | Enumeration-safe reset request response | TASK-020 |
| AC-005.2 | All sessions invalidated on reset completion | TASK-021 |
| AC-007.x | Self-only profile access; 403 on cross-user; output-encoded | TASK-025 |
| AC-008.1/.2 | Deactivation invalidates all sessions immediately | TASK-027 |
| AC-008.4 | 403 for non-admin on admin endpoints | TASK-028 |
| AC-009.3 | Non-empty body, sanitized pre-storage (threads) | TASK-032 |
| AC-010.2 | 423 on reply to locked thread | TASK-034 |
| AC-012.3 | Hidden content excluded from non-moderator views | TASK-035 |
| AC-013.2/.3 | Non-author edit → 403 | TASK-035 |
| AC-014.3/.4 | Immutable audit record per moderation action | TASK-037 |
| AC-015.2 | 409 on duplicate `(reporter_id, target_id)` report | TASK-036 |
| AC-016.1/.3 | Post create with sanitization | TASK-039 |
| AC-017.1 | Draft visible only to author/admin | TASK-041 |
| AC-019.3 | 404 on non-owner draft access | TASK-041 |
| AC-022.2/.3 | KB article: 403 for non-Contributor; sanitized | TASK-044 |
| AC-023.1/.2 | KB approve → visible + event; reject → draft + note | TASK-045 |
| AC-025.3 | 404 for unapproved KB on non-privileged direct access | TASK-046 |
| AC-026.1/.2 | Append-only revisions, restricted access | TASK-047 |
| AC-027.3/.4 | Search empty-state; no injection vector | TASK-050 |
| AC-027.5 | Hidden/unapproved content excluded from search index | TASK-049 |
| AC-028.2 | Archived category not selectable for new; preserved on existing | TASK-030 |
| AC-029.2 | Opt-out honored in notification dispatch | TASK-054 |
| AC-030.x | Dashboard admin-only; figures match source | TASK-056 |
| AC-031.2 | 429 generic message on rate-limit threshold breach | TASK-058 |
| AC-032.1/.2 | Role change effective without re-login | TASK-029 |
| AC-033.x | Unauthenticated → 401/redirect; post-login restore URL | TASK-022–023 |
| NFR-01 | Security | Deny access by default. All protected endpoints require valid JWT. Role-based authorization enforced server-side. WAF in front of ALB. No hardcoded secrets. (TASK-022, TASK-006) |
| NFR-003 | Cookie Security | Session cookie: `HttpOnly; Secure; SameSite=Strict`. (TASK-014, VER-007) |
| NFR-004 | CSRF | CSRF token required on all state-changing endpoints. (TASK-059, VER-014) |
| NFR-005 | Security Headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options on all responses. (TASK-008, VER-013) |
| NFR-016 | Log Correlation | Structured JSON logs include `correlationId` on every request. (TASK-005) |
| NFR-019 | Responsive | No layout breakage at defined mobile/tablet/desktop breakpoints. (TASK-061, VER-023) |
## Functional Requirements
### FR-01 — Identity & Session Management
### FR-02 — User Profiles

### FR-03 — Content Publishing
- **FR-03.1** Authenticated users can create, read, update, and soft-delete content items (articles / posts).
- **FR-03.2** Content body is sanitised server-side at the API boundary using an approved library (pending DEC-001/DEC-003) before persistence.
- **FR-03.3** Content supports versioning: each update creates a new revision; previous revisions are retrievable.
- **FR-03.4** Content can be in states: `draft`, `published`, `archived`, `flagged`. Only published content is visible to unauthenticated users.
- **FR-03.5** Users can upload media attachments (images) linked to a content item. Media is stored in S3.
- **FR-03.6** A moderation queue lists `flagged` content for administrator review.
- **FR-03.7** Content APIs (create, list, filter, version history) are covered by automated test suites (STORY-024, STORY-028, STORY-032).




### FR-07 — Infrastructure
- **FR-07.1** All AWS resources are declared in OpenTofu IaC under `infra/`. There is no clickops configuration.
- **FR-07.2** Infrastructure is parameterised per environment: `infra/envs/beta/` and `infra/envs/prod/` each have their own var-files and remote state configuration.
- **FR-07.3** VPC with public and private subnets, NAT gateway, Internet Gateway, and security groups is provisioned by IaC.
- **FR-07.4** ECS cluster (Fargate), ECR repositories, Aurora cluster, ElastiCache cluster, S3 buckets, OpenSearch domain, SQS queues, EventBridge custom bus, SES identity, WAF Web ACL, CloudWatch log groups, and X-Ray are all provisioned by IaC.
- **FR-07.5** Observability baseline (CloudWatch dashboards, alarms, X-Ray sampling rules) is defined in IaC (STORY-006–007).

---

## Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-02 | Availability | Aurora multi-AZ. ElastiCache with replica. ECS service auto-scaling with ≥ 2 tasks per service in prod. ALB health checks with unhealthy threshold = 2. Target SLA: TBD. |
| NFR-03 | Observability | Structured JSON logs with `correlationId` on every request. CloudWatch log groups per service. X-Ray traces across API → Worker hops. CloudWatch alarms for error rates and p99 latency. |
| NFR-04 | Scalability | ECS Fargate auto-scaling on CPU/memory. Aurora Serverless v2 ACU auto-scaling. ElastiCache horizontal replicas. OpenSearch scaling pending DEC-006. |
| NFR-05 | Testability | Unit tests per service. Integration tests per API route. E2E tests (Sprint 8). Security tests (Sprint 8). Accessibility tests (Sprint 8). |
| NFR-06 | AWS-only | All runtime infrastructure in approved AWS accounts/regions. IAM roles for workload identity. No long-lived access keys in application code. |
| NFR-07 | Content Safety | All user-supplied HTML/markup sanitised server-side before persistence. Approved sanitiser library required (DEC-001/DEC-003). |
| NFR-08 | Data Encryption | TLS 1.2+ for all data in transit (ALB, Aurora, Redis TLS, OpenSearch HTTPS). AES-256 encryption at rest for Aurora, S3, ElastiCache, OpenSearch volumes. KMS CMK where required by policy. |
| NFR-09 | Dependency Management | Lockfiles committed. CI runs SCA (software composition analysis) for known vulnerabilities on every PR. SBOM generated on release. |
| NFR-10 | Secrets Management | All secrets stored in AWS Secrets Manager. ECS task definitions reference Secrets Manager ARNs. No secrets in environment variable literals, logs, or container images. |

---

## Constraints

- **C-01:** AWS is the only approved cloud provider. No Azure, GCP, or multi-cloud patterns.
- **C-02:** IaC toolchain must be OpenTofu (Terraform-compatible) targeting AWS provider only.
- **C-03:** Content sanitiser library selection requires security review approval (DEC-001/DEC-003) before production deployment.
- **C-04:** Compute platform final selection (DEC-005) must be confirmed before Sprint 1 production provisioning.
- **C-05:** OpenSearch cluster sizing (DEC-006) must be confirmed before Sprint 6 production provisioning.
- **C-06:** Notification channel scope beyond SES email (DEC-002) must be confirmed before Sprint 7 production provisioning.

---

## Assumptions

- **A-01:** AWS SES is pre-configured (domain identity verified, production send limit raised) before Sprint 2 launch.
- **A-02:** AWS accounts for beta and prod are separate. Cross-account access patterns use IAM role assumption, not shared credentials.
- **A-03:** CI/CD pipeline (external to this project scope) can pull images from ECR and invoke `tofu apply` with appropriate IAM permissions.
- **A-04:** All developers work from macOS or Linux environments. Windows support is not a hard requirement.
- **A-05:** The project uses a Node.js monorepo (npm workspaces). The specific backend framework is TBD pending DEC-005.

---

## Acceptance Criteria (sprint-level)

| Sprint | Acceptance Gate |
|--------|----------------|
| Sprint 1 | All IaC applies cleanly to beta. ECS service is healthy. CloudWatch dashboards show metrics. WAF is active. |
| Sprint 2 | Register, login, logout, refresh, revoke, and password-recovery flows pass automated test suite (STORY-013). No unauthenticated access to protected routes. |
| Sprint 3 | Profile CRUD and avatar upload pass automated test suite (STORY-019). Authorization: users cannot modify other users' profiles. |
| Sprint 4–5 | Content create/edit/delete/version/list pass test suites (STORY-024, 028, 032). Sanitiser rejects XSS payloads. Media upload works. |
| Sprint 6 | Search queries return relevant results from OpenSearch. Indexing lag < 5 seconds for published content (TBD on SLA). Test suite passes (STORY-036). |
| Sprint 7 | Notification dispatch via SES confirmed in beta. Admin role management and audit log confirmed. Test suites pass (STORY-039, 041). |
| Sprint 8 | E2E suite (STORY-044), security suite (STORY-045), and accessibility suite (STORY-046) all pass in beta environment. |
| Sprint 9 | Production readiness review passed. All IaC applies cleanly to prod. Runbook documented. Launch approved. |
