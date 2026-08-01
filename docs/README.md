# Project Platform

> A full-featured, AWS-native community platform delivering identity management, discussion threads, knowledge-base authoring, full-text search, notifications, and administrative capabilities — designed for security, scalability, and operational excellence.

## Overview

This platform is a multi-component web application built entirely on AWS-managed services. It provides end-to-end workflows for user identity and session management, user profiles and avatars, discussion threads, knowledge-base articles with an approval workflow, full-text search, and event-driven notifications — all backed by a hardened infrastructure layer with observability and WAF protection baked in.

The system is intended for organisations that need a production-grade, cloud-native foundation that can be stood up quickly, extended safely, and operated with confidence. It targets two deployed environments — **beta** (pre-production) and **prod** (production) — with infrastructure-as-code driving both.

Security is a first-class concern: authentication and authorisation precede every API surface, secrets are stored in AWS Secrets Manager, and all data in transit and at rest is encrypted. The architecture follows a deny-by-default access model throughout.

The backend is implemented in **Python 3.12 with FastAPI** managed by **Poetry / setuptools**, with **Alembic** for database migrations and **pytest** for automated testing. The frontend is a **React 18 + TypeScript** SPA built with **Vite** and a custom design-system component library. Infrastructure is declared in **OpenTofu / Terraform** and deploys exclusively to AWS.

## Key Features

- **Identity & Session Management** — Registration, email verification, login, MFA, lockout, password reset, session invalidation, deny-by-default access gating (EPIC-002)
- **User Profiles** — Profile view/edit, pre-signed S3 avatar upload (EPIC-003)
- **Discussion & Moderation** — Thread/reply CRUD, lock/hide state, report intake, moderation queue and action audit trail (EPIC-004)
- **Posts** — Post/draft/comment CRUD with publish-state events (EPIC-005)
- **Knowledge Base** — Contributor article authoring, moderator/admin approval workflow, revision history (EPIC-006)
- **Full-Text Search** — Event-driven OpenSearch indexing pipeline, role-aware visibility filtering, reconciliation job (EPIC-007)
- **Notifications** — User preference API, SQS/Lambda dispatch worker (email + in-portal) honoring opt-out (EPIC-008)
- **Administration** — Account/role management, taxonomy management, cross-content aggregation dashboard (EPIC-003, EPIC-009)
- **Hardened Infrastructure** — VPC, ECS/Fargate, Aurora, ElastiCache, S3, WAF, CloudWatch, X-Ray, CI/CD security gates (EPIC-001)
- **Quality Gates** — Fine-grained rate limiting, CSRF/header hardening, WCAG 2.1 AA accessibility, E2E critical-journey and security audit suites (EPIC-010)

## Role Model

The platform enforces five distinct roles with server-side, per-request authorization:

| Role | Capabilities |
|------|-------------|
| **Guest** | Read published content; search |
| **Member** | All Guest capabilities + create discussions/posts, manage own profile |
| **Contributor** | All Member capabilities + author KB articles |
| **Moderator** | All Member capabilities + moderate content, work the moderation queue |
| **Admin** | Full access — account management, role assignment, taxonomy, dashboard |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Compute | AWS ECS / Fargate |
| API / Backend | Python 3.12, FastAPI 0.111+, Uvicorn |
| ORM / Migrations | SQLAlchemy 2.x, Alembic |
| Frontend | React 18, TypeScript 5, Vite 6, Tailwind CSS |
| Design System | Custom component library (`frontend/src/design-system/`) with Storybook 8 |
| Test — Backend | pytest 8, pytest-asyncio, httpx |
| Test — Frontend | Vitest, Playwright (a11y), Testing Library |
| Relational Database | AWS Aurora (PostgreSQL 15.x) |
| Cache / Session Store | AWS ElastiCache (Redis) via `redis-py` with `hiredis` |
| Object Storage | AWS S3 |
| Search | AWS OpenSearch Service |
| Messaging / Events | AWS SQS + EventBridge |
| Email Delivery | AWS SES |
| CDN / Edge | AWS WAF + ALB |
| Secrets | AWS Secrets Manager |
| Observability | AWS CloudWatch + X-Ray |
| IaC | OpenTofu / Terraform (AWS provider only) |
| Container Registry | AWS ECR |
| CI/CD | GitHub Actions (`.github/workflows/`) |

## Repository Structure

```text
project-root/
├── backend/                        - Python/FastAPI application
│   ├── app/                        - Application source code
│   │   ├── main.py                 - FastAPI app factory and startup
│   │   ├── core/                   - Config, DB, Redis, logging, security
│   │   ├── models/                 - SQLAlchemy ORM models
│   │   ├── schemas/                - Pydantic request/response schemas
│   │   ├── routers/                - FastAPI route definitions
│   │   ├── services/               - Business logic services
│   │   │   ├── identity/           - Register/login/MFA/session/reset
│   │   │   ├── profile/            - Profile CRUD
│   │   │   ├── admin/              - Account management, roles, dashboard
│   │   │   ├── discussion/         - Thread/reply/visibility
│   │   │   ├── moderation/         - Report intake and actions
│   │   │   ├── posts/              - Post/draft/comment CRUD
│   │   │   ├── kb/                 - KB article authoring and approval
│   │   │   ├── search/             - OpenSearch indexing and query
│   │   │   ├── notifications/      - Preference API and dispatch
│   │   │   └── media/              - Pre-signed S3 URL adapter
│   │   ├── middleware/             - CSRF, rate limiting, security headers
│   │   ├── auth/                   - JWT helpers and dependencies
│   │   └── api/                    - Admin router and API-level utilities
│   ├── alembic/                    - Database migrations (Alembic)
│   │   └── versions/               - Migration scripts
│   ├── services/                   - Standalone service modules
│   │   ├── identity/               - Cookie and session-store client
│   │   └── search/                 - Search reconciliation and scheduler
│   ├── tests/                      - pytest test suites
│   │   ├── e2e/                    - End-to-end journey tests (JRN-001–003)
│   │   ├── identity/               - Session/cookie tests
│   │   ├── posts/                  - Post-service tests
│   │   ├── profile_admin/          - Authorization matrix tests
│   │   ├── search/                 - Search injection/visibility tests
│   │   ├── security/               - IaC scanner, log audit, pipeline gate tests
│   │   └── services/               - KB, discussion, search unit tests
│   ├── scripts/                    - Operational scripts (e.g. capture_gate_evidence.sh)
│   ├── pyproject.toml              - Python project manifest (Poetry / setuptools)
│   ├── alembic.ini                 - Alembic configuration
│   └── pytest.ini                  - pytest configuration
├── frontend/                       - React/Vite SPA
│   ├── src/
│   │   ├── design-system/          - Reusable UI primitives (Button, Card, etc.)
│   │   ├── components/             - Feature-level components (admin dashboard)
│   │   ├── app/                    - App shell, layout, pages
│   │   ├── lib/                    - API clients, utilities
│   │   └── middleware/             - Admin route guard
│   ├── tests/
│   │   ├── a11y/                   - Playwright accessibility tests
│   │   └── admin-dashboard/        - Dashboard unit/integration tests
│   ├── .storybook/                 - Storybook configuration
│   ├── package.json                - npm scripts and dependencies
│   └── tailwind.config.ts          - Tailwind CSS configuration
├── .github/
│   └── workflows/                  - GitHub Actions CI/CD
│       ├── ci.yml                  - Main build/test/SAST/SCA pipeline
│       ├── security-gates.yml      - Security scanning gate
│       ├── identity-tests.yml      - Identity test suite gate
│       ├── phase-024-discussion-tests.yml - Discussion test suite gate
│       └── frontend-tests.yml      - Frontend test suite gate
├── docs/                           - Project documentation (this directory)
│   ├── README.md                   - Project overview (this file)
│   ├── architecture.md             - Architecture narrative and diagrams
│   ├── getting-started.md          - Setup, local dev, and deployment guide
│   ├── decision-log.md             - Intent, requirements summary, design decisions
│   ├── requirements.md             - Full generated requirements
│   ├── plan.md                     - Full generated plan
│   ├── design.md                   - Full generated design
│   └── contributing.md             - Contribution guidelines
├── .env.example                    - Local dev environment variable template
├── .env.beta.example               - Beta environment variable template
└── .env.prod.example               - Prod environment variable template
```

> See [Architecture](./architecture.md) · [Getting Started](./getting-started.md) · [Decision Log](./decision-log.md) · [Requirements](./requirements.md) · [Plan](./plan.md) · [Design](./design.md)

---

## Story-to-Feature Traceability

The table below maps each user-facing story to its epic, sprint, and the primary source files it touches. This provides a quick orientation for new engineers.

| Story | Epic | Sprint | Description | Primary Path(s) |
|-------|------|--------|-------------|-----------------|
| STORY-001 | EPIC-001 | 1 | VPC & Network Foundation | `infra/network/`, `infra/iam/` |
| STORY-002 | EPIC-001 | 1 | IaC Baseline & CI/CD Security Gates | `.github/workflows/`, `infra/ci/` |
| STORY-003 | EPIC-001 | 1 | Observability Baseline | `infra/observability/` |
| STORY-004 | EPIC-001 | 1 | API Edge: TLS, WAF, Security Headers | `infra/edge/`, `infra/waf/`, `backend/app/middleware/security_headers.py` |
| STORY-005 | EPIC-001 | 1 | Shared Design-System Component Library | `frontend/src/design-system/` |
| STORY-006 | EPIC-001 | 1 | Aurora & ElastiCache Provisioning | `infra/data/` |
| STORY-007 | EPIC-001 | 1 | Foundation Pipeline & Infra Security Validation | `backend/tests/security/`, `backend/tests/fixtures/` |
| STORY-008 | EPIC-002 | 2 | Session Store Integration | `backend/services/identity/session_store.py`, `backend/services/identity/cookie.py` |
| STORY-009 | EPIC-002 | 2 | Registration & Email Verification | `backend/app/services/identity/register.py`, `backend/app/services/identity/verify.py` |
| STORY-010 | EPIC-002 | 2 | Login, MFA & Account Lockout | `backend/app/services/identity/login.py`, `backend/app/services/identity/mfa.py`, `backend/app/services/identity/lockout.py` |
| STORY-011 | EPIC-002 | 2 | Password Reset & All-Session Invalidation | `backend/app/services/identity/` |
| STORY-012 | EPIC-002 | 2 | Access-Gating & Unauthenticated Route Protection | `backend/app/auth/dependencies.py`, `frontend/src/middleware/adminGuard.ts` |
| STORY-013 | EPIC-002 | 2 | Auth/Session Security Test Suite | `backend/tests/identity/`, `backend/tests/test_register.py`, `backend/tests/test_login_service.py` |
| STORY-014 | EPIC-003 | 3 | Member Profile View/Edit | `backend/app/services/profile/` |
| STORY-015 | EPIC-003 | 3 | Media/Asset Adapter — Pre-signed Avatar Upload | `backend/app/services/media/` |
| STORY-016 | EPIC-003 | 3 | Admin Account Management | `backend/app/services/admin/` |
| STORY-017 | EPIC-003 | 3 | Admin Role Assignment | `backend/app/services/admin/roles.py` |
| STORY-018 | EPIC-003 | 3 | Taxonomy Management (Categories/Tags) | `backend/app/services/admin/taxonomy_service.py` |
| STORY-019 | EPIC-003 | 3 | Profile/Admin/Taxonomy Authorization Tests | `backend/tests/profile_admin/` |
| STORY-020 | EPIC-004 | 4 | Discussion Thread CRUD & Listing | `backend/app/services/discussion_service.py`, `backend/app/routers/discussions.py` |
| STORY-021 | EPIC-004 | 4 | Discussion Reply, Lock & Hide State | `backend/app/services/discussion/replies.py`, `backend/app/services/discussion/visibility.py` |
| STORY-022 | EPIC-004 | 5 | Moderation Report Intake | `backend/app/services/moderation/reports.py` |
| STORY-023 | EPIC-004 | 5 | Moderation Review Queue & Actions | `backend/app/services/moderation/actions.py` |
| STORY-024 | EPIC-004 | 5 | Discussion & Moderation Test Suite | `backend/tests/test_moderation.py`, `backend/tests/routers/` |
| STORY-025 | EPIC-005 | 4 | Post/Draft CRUD & Listing | `backend/app/services/posts/` |
| STORY-026 | EPIC-005 | 4 | Draft Visibility & Ownership Enforcement | `backend/app/services/posts/visibility.py` |
| STORY-027 | EPIC-005 | 5 | Post Comments & Publish Event | `backend/app/services/posts/comments_service.py` |
| STORY-028 | EPIC-005 | 5 | Post Service Test Suite | `backend/tests/posts/` |
| STORY-029 | EPIC-006 | 4 | KB Article Authoring (Contributor Role) | `backend/app/services/kb/`, `backend/app/kb/` |
| STORY-030 | EPIC-006 | 5 | KB Approval/Rejection Workflow | `backend/app/services/kb/approval.py` |
| STORY-031 | EPIC-006 | 5 | KB Revision History | `backend/app/api/routes/kb_revisions.py` |
| STORY-032 | EPIC-006 | 5 | KB Service Test Suite | `backend/tests/test_kb_articles.py`, `backend/tests/services/kb/` |
| STORY-033 | EPIC-007 | 6 | Search Indexing Pipeline | `backend/app/services/search/subscriber.py` |
| STORY-034 | EPIC-007 | 6 | Search Query API & Visibility Filtering | `backend/app/services/search/query.py`, `backend/app/services/search/router.py` |
| STORY-035 | EPIC-007 | 6 | Search Index Reconciliation Job | `backend/services/search/reconcile.py`, `backend/services/search/scheduler.py` |
| STORY-036 | EPIC-007 | 6 | Search Relevance & Visibility Test Suite | `backend/tests/search/` |
| STORY-037 | EPIC-008 | 7 | Notification Preference API | `backend/app/services/notifications/router.py` |
| STORY-038 | EPIC-008 | 7 | Notification Dispatch Worker | `backend/app/services/notification_service.py` |
| STORY-039 | EPIC-008 | 7 | Notification Dispatch Test Suite | `backend/tests/test_notification_router.py`, `backend/tests/test_notification_repository.py` |
| STORY-040 | EPIC-009 | 7 | Admin Dashboard Aggregation Logic & Screen | `backend/app/services/admin/dashboard.py`, `frontend/src/components/admin/dashboard/` |
| STORY-041 | EPIC-009 | 7 | Admin Dashboard Test Suite | `backend/tests/test_admin_dashboard.py`, `frontend/tests/admin-dashboard/` |
| STORY-042 | EPIC-010 | 7 | Fine-Grained Rate Limiting & Abuse Controls | `backend/app/middleware/ratelimit.py` |
| STORY-043 | EPIC-010 | 7 | CSRF & Security Headers Hardening Review | `backend/app/middleware/csrf.py`, `backend/tests/test_csrf_middleware.py` |
| STORY-044 | EPIC-010 | 8 | Accessibility (WCAG 2.1 AA) & Responsive Verification | `frontend/tests/a11y/` |
| STORY-045 | EPIC-010 | 8 | End-to-End Critical Journey Verification | `backend/tests/e2e/` |
| STORY-046 | EPIC-010 | 8 | Security Review — Log Content, Secrets, IaC Audit | `backend/tests/security/`, `backend/app/security/` |
| STORY-047–051 | EPIC-011 | 9 | Documentation Suite | `docs/` |

## Delivery Model

The project is delivered in **9 sprints** across **23 commit slices** (SLICE-001–SLICE-023). Each slice is reviewable and mergeable independently. Sprint 9 (SLICE-023) is this documentation suite. See [Plan](./plan.md) for the full sprint/phase breakdown and [Decision Log](./decision-log.md) for the slice-to-commit map.
