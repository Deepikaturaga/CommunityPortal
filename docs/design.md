# Generated Design

> This document preserves the generated design, updated to reflect the Phase 3 component model (COMP-001–012), store IDs (STORE-001–009), interface IDs (IF-001–017), and verification IDs (VER-001–024). See [Requirements](./requirements.md) for what is being built, [Plan](./plan.md) for the delivery sequence, and [Decision Log](./decision-log.md) for key trade-offs and open decisions.

---

- Failed-attempt lockout triggers at configurable threshold; owner alert dispatched via SES (TASK-018).
- MFA challenge/verify: `services/identity/mfa.*` — invalid/expired factor rejected and logged (TASK-019).
- Password reset endpoint (`services/identity/reset.*`) returns identical response regardless of email existence (TASK-020).
- Reset completion invalidates all Redis session keys for the account immediately (TASK-021).

**Interfaces:**
- **IF-001** `POST /api/v1/auth/register` — registration with uniqueness + password policy + sanitization
- **IF-002** `POST /api/v1/auth/login` — login with generic failure response + account-status check
- **IF-003** `GET/PUT /api/v1/profile` — self-only profile CRUD
- **IF-013** Pre-signed S3 PUT/GET URL — issued by `services/media/` (COMP-011)

**Session design (TASK-013/014):**
- Session store: `services/identity/session-store.*` — create, read, expire, invalidate operations backed by ElastiCache Redis.
- Cookie: `HttpOnly; Secure; SameSite=Strict` (NFR-003).
- Invalidation: explicit delete of Redis key; bulk invalidation on password reset and admin deactivation.

**Deny-by-default auth middleware (TASK-022):**
- `services/*/middleware/authn.*` — every protected route checks JWT validity and session state before handler execution.
- Unauthenticated requests → 401 / redirect to `/login`.
- Post-login redirect restores original URL (`web/src/routing/guards.*`, TASK-023).
- Private bucket, no public ACL (TASK-026, VER-021).

---

### 3.2a Admin Component (COMP-009) — Account & Role Management

**Responsibilities:** Account activate/deactivate/delete, forced session invalidation, Moderator/Contributor role assignment/revocation, taxonomy management, cross-content aggregation dashboard.

**Service path:** `services/admin/`

**Sub-modules:**
- `services/admin/accounts.*` — account status endpoints; deactivation immediately invalidates all Redis session keys (TASK-027).
- `services/admin/middleware/authz.*` — 403 for non-admin on all `admin/*` endpoints (TASK-028).
- `services/admin/roles.*` — role assign/revoke with per-request DB re-evaluation (no cached role in token) (TASK-029).
- `services/admin/taxonomy.*` — category/tag CRUD + archive; `STORE-009`; soft-state archive (TASK-030).
- `services/admin/dashboard.*` — aggregation queries across accounts, content volume, moderation stats (TASK-056).
> **Phase 3 refinement:** Content has been split into three distinct components — COMP-003 (Discussion), COMP-004 (Posts), COMP-005 (KB Articles) — each with its own service path and state machine. The shared moderation capability is COMP-006 (`services/moderation/`). The legacy COMP-003 label is retained in the table below for backward-reference; the canonical design uses the split model.

---

### 3.3a Discussion Component (COMP-003)

**Service path:** `services/discussion/`

**Data model (Aurora — `STORE-003`):**

| Table | Key Columns |
|-------|-------------|
| `threads` | `id (uuid PK)`, `author_id (FK)`, `category_id (FK → STORE-009)`, `title`, `body_sanitised`, `status (enum: open/locked/hidden)`, `created_at`, `updated_at` |
| `replies` | `id (uuid PK)`, `thread_id (FK)`, `author_id (FK)`, `body_sanitised`, `hidden`, `created_at`, `updated_at` |

**Interfaces:**
- **IF-004** Thread create/list/filter/sort — `services/discussion/threads.*` (TASK-032)
- **IF-017** ContentCreated EventBridge event on thread creation (TASK-033)
- Reply endpoint: `services/discussion/replies.*` — 423 on locked thread (TASK-034)
- Visibility filter: `services/discussion/visibility.*` — hidden excluded from non-moderator views; non-author edit → 403 (TASK-035)

---

### 3.3b Moderation Component (COMP-006)

**Service path:** `services/moderation/`

**Data model (Aurora — `STORE-006`):**

| Table | Key Columns |
|-------|-------------|
| `reports` | `id (uuid PK)`, `reporter_id (FK)`, `target_type`, `target_id`, `reason`, `created_at`, UNIQUE `(reporter_id, target_id)` |
| `moderation_actions` | `id (uuid PK)`, `actor_id (FK)`, `action (enum: lock/hide/delete)`, `target_type`, `target_id`, `created_at` (immutable append-only) |

**Interfaces:**
- **IF-008** Report intake — `services/moderation/reports.*`; 409 on duplicate `(reporter_id, target_id)` (TASK-036)
- **IF-009** Queue listing + lock/hide/delete — `services/moderation/actions.*`; 403 for non-moderator; every action writes immutable audit record (TASK-037)

---

### 3.3c Posts Component (COMP-004)

**Service path:** `services/posts/`

**Data model (Aurora — `STORE-004`):**

| Table | Key Columns |
|-------|-------------|
| `posts` | `id (uuid PK)`, `author_id (FK)`, `title`, `body_sanitised`, `status (enum: draft/published)`, `category_id (FK)`, `created_at`, `updated_at` |
| `comments` | `id (uuid PK)`, `post_id (FK)`, `author_id (FK)`, `body_sanitised`, `created_at` |

**Interfaces:**
- **IF-005** Post create (draft/publish) — `services/posts/posts.*`; sanitized pre-storage; `IF-017` event only on publish (TASK-039–040)
- Draft visibility filter — `services/posts/visibility.*`; 404 on non-owner draft access (TASK-041)
- Comment create — `services/posts/comments.*`; `IF-017` event for notification consumers (TASK-042)

---

### 3.3d Knowledge Base Component (COMP-005)

**Service path:** `services/kb/`


> **Phase 3 refinement:** The KB uses a dedicated `STORE-005` with article-specific columns and approval state:

| Table | Key Columns |
|-------|-------------|
| `kb_articles` | `id (uuid PK)`, `author_id (FK)`, `title`, `body_sanitised`, `status (enum: draft/pending/approved/rejected)`, `category_id (FK)`, `created_at`, `updated_at` |
| `kb_revisions` | `id (uuid PK)`, `article_id (FK)`, `body_raw`, `body_sanitised`, `revision_number`, `editor_id (FK)`, `created_at` (immutable append-only) |

**Interfaces:**
- **IF-007** Article create — `services/kb/articles.*`; Contributor-role check (403 non-Contributor); sanitized pre-storage (TASK-044)
- **IF-006** Revision history — `services/kb/revisions.*`; restricted to author/moderator/admin (TASK-047)
- Approval — `services/kb/approval.*`; approve → visible + EventBridge index event; reject → draft + note (TASK-045)
- Visibility — `services/kb/visibility.*`; 404 for unapproved on non-privileged direct access (TASK-046)
         flagged ──► (admin: approve → published | reject → archived)

KB article state machine:
draft ──► pending_approval ──► approved (visible to all)
              │
              ▼
           rejected → draft (with rejection note)
**EventBridge events emitted on content mutation (IF-017):**
- `kb.approved` — triggers OpenSearch index upsert (TASK-045)
- `thread.created` — triggers OpenSearch index upsert (TASK-033)
- `post.published` — triggers OpenSearch index upsert (TASK-040)
- `comment.created` — triggers notification dispatch (TASK-042)
**Service path:** `services/search/`

      "entity_type": { "type": "keyword" },
      "version": { "type": "long" },
**Idempotency key:** `(entity_type, entity_id, version)` — enables safe SQS-redelivery and full-reindex reconciliation (TASK-049/051).

**Hidden/unapproved exclusion:** Event consumer checks `status` / `hidden` flags before indexing; hidden or unapproved content is never written to the index (AC-027.5).

- **IF-014** `GET /api/v1/search?q=<keyword>&author=<id>&from=<date>&to=<date>&type=<type>&page=<n>&size=<n>`
- Returns: `{ hits: [...], total: n, facets: { author: [...], type: [...] } }`
- Parameterized query — no injection vector (AC-027.4, VER-003, VER-009).
- Role-aware visibility filter applied before returning results (TASK-050).
- Empty-state response when no results (AC-027.3).
5. **Reconciliation job** (`services/search/reconcile.*`, TASK-051): scheduled/manual full-reindex producing identical index state on re-run (idempotent upsert by `entity_type + entity_id + version`).
**Service path:** `services/notifications/` (preference API) + `workers/notifications/dispatch.*` (SQS dispatch worker, TASK-054)


**Opt-out:** If user has opted out for the event type, dispatch is skipped silently (AC-029.2).
**SES failure fallback:** If SES delivery fails, the event is recorded as in-portal only — no user-facing error (TASK-054).

**Interfaces:**
- **IF-010** `GET/PUT /api/v1/notifications/preferences` — self-only preference management (TASK-053)
- **IF-012** SQS consumer/Lambda dispatch worker — `workers/notifications/dispatch.*` (TASK-054)
> **Phase 3 note:** COMP-006 (in the original design) has been superseded by two separate components: COMP-006 (Moderation, `services/moderation/`) and COMP-009 (Admin, `services/admin/`). See §3.2a and §3.3b above. The legacy component table entry is retained for backward-reference.


### 3.7 Media Adapter (COMP-011)

**Service path:** `services/media/`

**Responsibilities:** Issue time-limited pre-signed S3 PUT/GET URLs for avatar and media uploads. Validates content-type and enforces size limit via `Content-Length-Range` condition in the pre-signed URL policy.

**Security:** Private S3 bucket — no public ACL; no direct public access. URL expiry: TBD (DEC-004 will set the window). (TASK-026, VER-021)

**Interface:**
- **IF-013** `POST /api/v1/media/upload-url` — issues pre-signed PUT URL with content-type + size constraints
- `GET /api/v1/media/download-url/:key` — issues pre-signed GET URL for authorized callers

---

### 3.8 Frontend Shell (COMP-010)

**Path:** `web/`

**Responsibilities:** React SPA consuming the API over HTTPS. Hosts the design-system component library and enforces deny-by-default route guards.

**Design-system package** (`web/src/design-system/`, TASK-009):
- Primitives: Button, Form, Input, Select, Pagination, EmptyState, ErrorState, PermissionDenied
- Rendered and accessibility-tested via Storybook (or equivalent)
- axe-core baseline scan in CI (VER-022 prep)

**Route guards** (`web/src/routing/guards.*`, TASK-023):
- Every protected route checks authentication state before rendering
- Unauthenticated → redirect to `/login` with `next` param capturing original URL
- Post-login redirect restores original URL (AC-033.2)

---

### 3.9 API Edge (COMP-012)

**Path:** `edge/middleware/headers.*` + `infra/edge/*.tf`

**Responsibilities:** TLS termination (ALB, TASK-007), security header injection (TASK-008), CORS policy enforcement, WAF integration (TASK-006). All responses carry CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options` (NFR-005). CSRF token middleware on all state-changing endpoints (`services/*/middleware/csrf.*`, TASK-059).

**Rate limiting middleware** (`services/*/middleware/ratelimit.*`, TASK-058): Per-account/per-window limits on registration, login, and content-creation endpoints; 429 with generic message on threshold breach (AC-031.2, VER-020).
> **Phase 3 refinements — canonical path prefix is `/api/v1/`:**

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/verify-email
POST   /api/v1/auth/mfa/verify
POST   /api/v1/auth/reset-password/request
POST   /api/v1/auth/reset-password/complete
GET/PUT /api/v1/profile
POST   /api/v1/media/upload-url
GET    /api/v1/media/download-url/:key
GET/POST /api/v1/discussions/threads
POST   /api/v1/discussions/threads/:id/replies
POST   /api/v1/discussions/reports
GET/POST /api/v1/posts
GET/POST /api/v1/posts/:id/comments
GET/POST /api/v1/kb/articles
GET    /api/v1/kb/articles/:id/revisions
GET    /api/v1/search
GET/PUT /api/v1/notifications/preferences
GET    /api/v1/admin/accounts
PUT    /api/v1/admin/accounts/:id/status
PUT    /api/v1/admin/roles/:userId
GET/POST/PUT/DELETE /api/v1/admin/taxonomy
GET    /api/v1/admin/dashboard
GET    /api/v1/admin/moderation/queue
POST   /api/v1/admin/moderation/:id/action
```

---

## 11. Store Inventory

| Store ID | Table(s) / Index | Component(s) | Notes |
|----------|-----------------|-------------|-------|
| STORE-001 | `users`, `refresh_tokens`, `password_reset_tokens` | COMP-001 | Aurora — users, sessions, password reset |
| STORE-002 | Redis key-value store | COMP-001, rate-limit middleware | ElastiCache — session TTLs, token blacklist, rate-limit counters |
| STORE-003 | `threads`, `replies` | COMP-003 | Aurora — discussions |
| STORE-004 | `posts`, `comments` | COMP-004 | Aurora — posts |
| STORE-005 | `kb_articles`, `kb_revisions` | COMP-005 | Aurora — KB articles + revision history |
| STORE-006 | `reports`, `moderation_actions` | COMP-006 | Aurora — moderation reports + immutable action log |
| STORE-007 | OpenSearch index | COMP-007 | OpenSearch Service — full-text search |
| STORE-008 | `notification_preferences`, `notification_log` | COMP-008 | Aurora — notification preferences + dispatch log |
| STORE-009 | `categories`, `tags` | COMP-009 | Aurora — taxonomy; supports archive soft-state |

---

## 12. Interface Inventory

| IF ID | Description | Endpoint / Mechanism | Component |
|-------|-------------|---------------------|-----------|
| IF-001 | Registration | `POST /api/v1/auth/register` | COMP-001 |
| IF-002 | Login | `POST /api/v1/auth/login` | COMP-001 |
| IF-003 | Profile CRUD | `GET/PUT /api/v1/profile` | COMP-002 |
| IF-004 | Thread CRUD | `GET/POST /api/v1/discussions/threads` | COMP-003 |
| IF-005 | Post CRUD | `GET/POST /api/v1/posts` | COMP-004 |
| IF-006 | KB revision history | `GET /api/v1/kb/articles/:id/revisions` | COMP-005 |
| IF-007 | KB article authoring | `POST /api/v1/kb/articles` | COMP-005 |
| IF-008 | Moderation report intake | `POST /api/v1/discussions/reports` | COMP-006 |
| IF-009 | Moderation queue + actions | `GET/POST /api/v1/admin/moderation/*` | COMP-006 |
| IF-010 | Notification preferences | `GET/PUT /api/v1/notifications/preferences` | COMP-008 |
| IF-011 | Admin account management | `GET/PUT /api/v1/admin/accounts/*` | COMP-009 |
| IF-012 | Notification dispatch worker | SQS consumer → SES / in-portal | COMP-008 |
| IF-013 | Media pre-signed URL | `POST /api/v1/media/upload-url` | COMP-011 |
| IF-014 | Search query | `GET /api/v1/search` | COMP-007 |
| IF-015 | Admin role management | `PUT /api/v1/admin/roles/:userId` | COMP-009 |
| IF-016 | Taxonomy management | `GET/POST/PUT/DELETE /api/v1/admin/taxonomy` | COMP-009 |
| IF-017 | ContentCreated / state-change EventBridge event | EventBridge → SQS → consumers | COMP-003/004/005 (publisher), COMP-007/008 (consumer) |

---

## 13. Verification Matrix

See [Decision Log — Verification Evidence Map](./decision-log.md#verification-evidence-map) for the full VER-001–VER-024 cross-reference table mapping each verification ID to its satisfying task(s).
## 1. Design Principles

1. **Security by default** — deny access at every boundary; validate all input; sanitise all output.
2. **AWS-native** — use managed services; minimise operational toil; rely on IAM for all cloud identity.
3. **Async decoupling** — the API write path must not block on search indexing or notification dispatch.
4. **Observability-first** — structured logs, distributed traces, and CloudWatch alarms from day one.
5. **Environment parity** — beta and prod are structurally identical; they differ only in sizing and secrets.
6. **IaC everything** — no clickops; all AWS resources are declared in OpenTofu.

---

## 2. System Boundaries and Trust Model

```
Internet ──► AWS WAF ──► ALB (public subnet) ──► API Service (private subnet)
                                                        │
                        Worker Service (private subnet) │
                                ▲                       │
                                └── SQS / EventBridge ──┘
                                          │
                          Aurora │ Redis │ S3 │ OpenSearch │ SES
                          (all in private subnet or VPC endpoint)

Admin users ──► same ALB path, role-checked server-side
```

Trust boundaries:
- **Untrusted:** all inbound internet traffic (WAF-filtered before reaching ALB).
- **Semi-trusted:** authenticated API clients (JWT-verified; resource-level authorization applied per endpoint).
- **Trusted internal:** Worker service (no public endpoint; consumes SQS only; IAM role-restricted).
- **Trusted AWS managed:** Aurora, Redis, S3, OpenSearch, SES, EventBridge, SQS (accessed via VPC endpoints where available; IAM + resource policies).

---

## 3. Component Design

### 3.1 Identity Component (COMP-001)

**Responsibilities:** registration, email verification, login, JWT issuance, refresh, revocation, password recovery, MFA scaffold.

**Data model (Aurora):**

| Table | Key Columns |
|-------|-------------|
| `users` | `id (uuid PK)`, `email (unique)`, `password_hash`, `email_verified_at`, `mfa_enabled`, `role`, `created_at`, `deleted_at` |
| `refresh_tokens` | `id (uuid PK)`, `user_id (FK)`, `token_hash`, `expires_at`, `revoked_at`, `created_at` |
| `password_reset_tokens` | `id (uuid PK)`, `user_id (FK)`, `token_hash`, `expires_at`, `used_at` |

**Redis usage:**
- Token blacklist: `SET token:<jti> 1 EX <remaining_seconds>` — allows immediate JWT revocation before expiry.
- Session store: refresh token lookup cache (optional layer on top of Aurora `refresh_tokens`).

**JWT design:**
- Access token: HS256 or RS256 (TBD), short-lived (`JWT_EXPIRY=15m`), contains `sub` (user_id), `role`, `jti`.
- Refresh token: opaque random string, hashed before storage in Aurora, long-lived (`REFRESH_TOKEN_EXPIRY=7d`).

**Email flows (SES):**
- Account verification: time-limited signed link (`/auth/verify-email?token=<signed_token>`).
- Password recovery: time-limited single-use link (`/auth/reset-password?token=<signed_token>`).

---

### 3.2 Profile Component (COMP-002)

**Responsibilities:** profile CRUD, avatar upload, visibility settings.

**Data model (Aurora):**

| Table | Key Columns |
|-------|-------------|
| `profiles` | `id (uuid PK)`, `user_id (FK, unique)`, `display_name`, `bio`, `avatar_s3_key`, `visibility`, `created_at`, `updated_at`, `deleted_at` |

**S3 key convention:** `avatars/{user_id}/{uuid}.{ext}` — pre-signed PUT URL issued by API; client uploads directly to S3.

**Validation:**
- `avatar_s3_key` MIME type validated via Content-Type header during pre-signed URL generation and confirmed via S3 event or post-upload verification.
- File size limit: TBD (DEC-004). Enforced via S3 pre-signed URL `Content-Length-Range` condition.

---

### 3.3 Content Component (COMP-003)

**Responsibilities:** content CRUD, state machine, server-side sanitisation, versioning, media attachments, moderation queue.

**Data model (Aurora):**

| Table | Key Columns |
|-------|-------------|
| `content_items` | `id (uuid PK)`, `author_id (FK)`, `title`, `body_sanitised`, `status (enum)`, `current_revision_id (FK)`, `created_at`, `updated_at`, `deleted_at` |
| `content_revisions` | `id (uuid PK)`, `content_id (FK)`, `body_raw`, `body_sanitised`, `revision_number`, `created_by (FK)`, `created_at` |
| `content_media` | `id (uuid PK)`, `content_id (FK)`, `s3_key`, `mime_type`, `size_bytes`, `created_at` |

**Content status state machine:**

```
draft ──► published ──► archived
           │
           ▼
```

**Sanitisation:** Applied to `body_raw` before writing `body_sanitised`. Library and whitelist config pending DEC-001/DEC-003. The sanitiser is called at the API service layer — not in the Worker.

- `content.published` — triggers OpenSearch index upsert
- `content.updated` — triggers OpenSearch index upsert
- `content.archived` / `content.deleted` — triggers OpenSearch index delete
- `content.flagged` — triggers notification to moderators

---

### 3.4 Search Component (COMP-004)

**Responsibilities:** full-text search query, result ranking, faceted filtering, async index maintenance.

**OpenSearch index design:**

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "title": { "type": "text", "analyzer": "english" },
      "body": { "type": "text", "analyzer": "english" },
      "author_id": { "type": "keyword" },
      "status": { "type": "keyword" },
      "created_at": { "type": "date" },
      "content_type": { "type": "keyword" }
    }
  }
}
```

**Query API:**

**Indexing pipeline:**
1. API emits EventBridge event on content state change.
2. EventBridge rule routes to SQS `search-index-queue`.
3. Worker consumes SQS, calls OpenSearch bulk API.
4. DLQ captures failures; CloudWatch alarm on DLQ depth.

---

### 3.5 Notification Component (COMP-005)

**Responsibilities:** preference management (API), event-driven dispatch (Worker), SES email delivery.

**Data model (Aurora):**

| Table | Key Columns |
|-------|-------------|
| `notification_preferences` | `id (uuid PK)`, `user_id (FK)`, `event_type`, `channel`, `enabled`, `updated_at` |
| `notification_log` | `id (uuid PK)`, `user_id (FK)`, `event_type`, `channel`, `status`, `sent_at`, `error` |

**Dispatch flow:**
1. Domain events published to EventBridge.
2. EventBridge rule routes to SQS `notification-queue`.
3. Worker reads user preferences from Aurora (or Redis cache).
4. If enabled for the user/event: Worker dispatches via SES (email) or SNS (push — pending DEC-002).
5. Outcome written to `notification_log`.

---

### 3.6 Administration Component (COMP-006)

**Responsibilities:** role management, content moderation console, audit log.

**Data model (Aurora):**

| Table | Key Columns |
|-------|-------------|
| `audit_log` | `id (uuid PK)`, `actor_id (FK)`, `action`, `resource_type`, `resource_id`, `before_state (jsonb)`, `after_state (jsonb)`, `ip_address`, `created_at` |

**Role model:**
- `user` — default; can manage own content and profile.
- `moderator` — can view flagged content; can approve/reject.
- `admin` — full access; can manage roles; can read all profiles; full audit log access.

**Audit log:** Append-only. Written by a middleware decorator on all privileged mutation endpoints. Read via `GET /admin/audit-log` with filters. No delete endpoint.

---

## 4. API Design

### Base conventions

- All endpoints: `Content-Type: application/json`
- Authentication: `Authorization: Bearer <access_token>`
- Error envelope: `{ "error": { "code": "string", "message": "string", "correlationId": "uuid" } }`
- Pagination: `?page=1&size=20` → `{ data: [...], meta: { page, size, total } }`

### Key endpoint groups

| Group | Base Path | Auth Required |
|-------|-----------|--------------|
| Identity | `/auth/*` | Varies (register/login: none; revoke/refresh: token) |
| Profiles | `/profiles/*` | Yes (own) / Admin-only (others) |
| Content | `/content/*` | Yes (write); No (public read of published) |
| Search | `/search` | No |
| Notifications | `/notifications/*` | Yes |
| Administration | `/admin/*` | Admin role required |

### Selected endpoints

```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
POST   /auth/revoke-all
POST   /auth/forgot-password
POST   /auth/reset-password
GET    /auth/verify-email

GET    /profiles/:userId
PUT    /profiles/:userId
DELETE /profiles/:userId
POST   /profiles/:userId/avatar

POST   /content
GET    /content
GET    /content/:id
PUT    /content/:id
DELETE /content/:id
GET    /content/:id/revisions
POST   /content/:id/media
GET    /content/:id/media

GET    /search

GET    /notifications/preferences
PUT    /notifications/preferences/:eventType

GET    /admin/users
PUT    /admin/users/:id/role
GET    /admin/content/flagged
PUT    /admin/content/:id/moderate
GET    /admin/audit-log
```

---

## 5. Infrastructure Design

### VPC Layout

```
Region: us-east-1 (2 AZs minimum)

Public Subnets:  ALB, NAT Gateway
Private Subnets: ECS Tasks (API, Worker), Aurora, ElastiCache, OpenSearch
```

### ECS Service Design

| Service | CPU | Memory | Min Tasks | Max Tasks |
|---------|-----|--------|-----------|-----------|
| API | 512 vCPU | 1024 MB | 2 (prod) / 1 (beta) | 10 |
| Worker | 256 vCPU | 512 MB | 1 | 5 |

Auto-scaling: target-tracking on CPU utilisation (target 60%).

### Aurora Configuration

| Parameter | Beta | Prod |
|-----------|------|------|
| Engine | Aurora PostgreSQL 15.x | Aurora PostgreSQL 15.x |
| Mode | Serverless v2 | Serverless v2 (or Provisioned — DEC-005) |
| Min ACU | 0.5 | 2 |
| Max ACU | 8 | 32 |
| Multi-AZ | 1 writer + 0 readers | 1 writer + 1 reader |
| Backup retention | 7 days | 30 days |

### Security Group Design

- ALB SG: inbound 443 from `0.0.0.0/0`; outbound to API SG on `PORT`.
- API SG: inbound from ALB SG only; outbound to Aurora SG, Redis SG, OpenSearch SG, HTTPS `0.0.0.0/0` (SES/S3/EventBridge via NAT).
- Worker SG: no inbound; outbound to Aurora SG, OpenSearch SG, HTTPS (SQS/SES/SNS via NAT or VPC endpoint).
- Aurora SG: inbound from API SG and Worker SG on port 5432 only.
- Redis SG: inbound from API SG on port 6379 only.
- OpenSearch SG: inbound from API SG and Worker SG on port 443 only.

---

## 6. Security Design

### Authentication & Authorization

- JWTs verified on every protected request via middleware.
- Role extracted from JWT `role` claim; re-verified against `users.role` in Aurora for privilege-sensitive operations.
- Token blacklist checked in Redis on every request (jti lookup) — enables immediate revocation.

### OWASP Top 10 Coverage

| Risk | Control |
|------|---------|
| A01 Broken Access Control | Deny-by-default middleware; resource-level owner checks; role checks on admin endpoints |
| A02 Cryptographic Failures | TLS 1.2+ everywhere; AES-256 at rest; KMS for Aurora/S3; bcrypt/argon2 for passwords |
| A03 Injection | ORM parameterised queries; input schema validation (zod or equivalent); sanitiser on content body |
| A04 Insecure Design | Threat model reviewed per component; abuse cases defined per API group |
| A05 Security Misconfiguration | WAF managed rules; security group least-privilege; S3 block-public-access; no debug endpoints in prod |
| A06 Vulnerable Components | SCA on every PR; lockfiles committed; SBOM generated on release (STORY-050) |
| A07 Auth Failures | Short JWT lifetime; Redis revocation; account lockout on repeated failures (TBD threshold); MFA scaffold |
| A08 Integrity Failures | Lockfiles; signed IaC artifacts; protected CI/CD pipeline; IaC plan review before apply |
| A09 Logging & Monitoring | Structured logs without PII/secrets; CloudWatch alarms; X-Ray traces; CloudTrail for AWS API calls |
| A10 SSRF | Worker egress restricted to known endpoints (SES, SNS, OpenSearch) via security group; no user-controlled outbound URLs |

---

## 7. Observability Design

### Logging

- Format: structured JSON.
- Required fields per log line: `timestamp`, `level`, `service`, `correlationId`, `traceId`, `spanId`.
- Sensitive data (passwords, tokens, PII) must never appear in log lines.
- Log groups per service: `/app/api`, `/app/worker`.
- Retention: 30 days beta / 90 days prod.

### Metrics (CloudWatch)

- API: `RequestCount`, `ErrorRate (4xx/5xx)`, `LatencyP50/P99`, `AuthFailures`.
- Worker: `MessagesProcessed`, `MessageFailures`, `DLQDepth`, `IndexingLag`.
- Aurora: `DatabaseConnections`, `CPUUtilization`, `ReadLatency`, `WriteLatency`.
- Redis: `CacheHits`, `CacheMisses`, `Evictions`.
- Alarms: 5xx error rate > 1% for 5 minutes; p99 latency > 2s for 5 minutes; DLQ depth > 0.

### Tracing (X-Ray)

- API service: X-Ray SDK middleware traces every HTTP request.
- Worker service: X-Ray SDK traces every SQS message processing cycle.
- Trace propagation: `X-Amzn-Trace-Id` header forwarded on all internal calls.

---

## 8. Data Design

### Encryption

| Data Store | In Transit | At Rest |
|------------|-----------|---------|
| Aurora | TLS (enforced by parameter group) | AES-256 (AWS-managed KMS key) |
| ElastiCache | TLS enabled | AES-256 (at-rest encryption) |
| S3 | HTTPS only (bucket policy) | SSE-S3 (AES-256) or SSE-KMS |
| OpenSearch | HTTPS only | AES-256 (node-to-node encryption) |

### Retention & Deletion

- Soft-delete pattern for users, profiles, and content (`deleted_at` timestamp).
- Hard delete: GDPR/right-to-erasure flow is TBD (post-MVP).
- Audit log: no delete endpoint; retention policy enforced by CloudWatch Logs retention setting.
- Refresh tokens: expired tokens purged by a scheduled Worker job (cron via EventBridge Scheduler — TBD).

---

## 9. IaC Structure

```
infra/
├── modules/
│   ├── vpc/                 - VPC, subnets, NAT, IGW, endpoints
│   ├── ecs-cluster/         - ECS cluster, capacity providers, ALB
│   ├── ecs-service/         - Reusable ECS service + task definition module
│   ├── aurora/              - Aurora cluster, parameter group, subnet group
│   ├── elasticache/         - ElastiCache Redis replication group
│   ├── s3/                  - S3 buckets with lifecycle policies
│   ├── opensearch/          - OpenSearch domain
│   ├── sqs/                 - SQS queues + DLQs
│   ├── eventbridge/         - EventBridge custom bus + rules
│   ├── waf/                 - WAF Web ACL + managed rule groups
│   ├── secrets/             - Secrets Manager secret placeholders
│   └── observability/       - CloudWatch dashboards, alarms, X-Ray groups
└── envs/
    ├── beta/
    │   ├── main.tf          - Root module calling sub-modules
    │   ├── beta.tfvars      - Beta-specific variable values
    │   └── backend.tf       - Remote state (S3 + DynamoDB lock)
    └── prod/
        ├── main.tf
        ├── prod.tfvars
        └── backend.tf
```

---

## 10. Open Decisions

| ID | Topic | Impact | Owner | Status |
|----|-------|--------|-------|--------|
| DEC-001 | Content sanitiser library (server-side) | Blocks STORY-020/025/029 production delivery | TBD | Open |
| DEC-002 | Notification channels beyond SES (SMS, Push) | Blocks STORY-038 production dispatch | TBD | Open |
| DEC-003 | Sanitiser HTML whitelist configuration | Blocks STORY-020/025/029 production delivery | TBD | Open |
| DEC-004 | Avatar / media file size limits | Minor — S3 pre-signed URL policy | TBD | Open |
| DEC-005 | Compute platform final lock-in (ECS vs EKS vs App Runner) | Blocks Sprint 1 production provisioning | TBD | Open |
| DEC-006 | OpenSearch cluster sizing and node type | Blocks Sprint 6 production provisioning | TBD | Open |

> Architecture and interface work may proceed for all open decisions. Production provisioning and library lock-in are gated on decision confirmation. See [Decision Log](./decision-log.md) for trade-off summaries.
