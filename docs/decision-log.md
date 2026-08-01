# Decision Log — Architecture Decision Records (ADRs)

> This document records every significant architectural, technology, and design decision
> made during the build of this project. Each entry captures **intent** (what problem we
> were solving), **requirements context** (the forces acting on the decision), **the
> decision itself**, **considered alternatives**, and **trade-offs / consequences**.
>
> Add a new ADR entry whenever a decision with lasting architectural impact is made.
> Decisions are immutable once they reach status **Accepted**; superseded decisions are
> marked **Superseded by ADR-XXX** rather than deleted.
>
> **Design Notes (DSN)** capture lower-level design choices and implementation details
> that do not rise to the level of a full ADR. They are cross-referenced by the ADR that
> owns their subject area and by architecture Section 2 (component model) and Section 16
> (security boundaries).
>
> **Decision Status Records (DEC)** provide a concise status snapshot for all in-flight
> and resolved decisions. Auditors and new team members should read this table first.

---

## Table of Contents

| ID | Title | Status |
|----|-------|--------|
| [ADR-001](#adr-001) | Frontend framework — Next.js 14 App Router with React Server Components | Accepted |
| [ADR-002](#adr-002) | Authentication transport — HTTP-only secure cookies (not bearer tokens) | Accepted |
| [ADR-003](#adr-003) | Backend framework — dedicated Express API service (not Next.js Route Handlers only) | Accepted |
| [ADR-004](#adr-004) | Database — Aurora PostgreSQL Serverless v2 | Accepted |
| [ADR-005](#adr-005) | Infrastructure-as-Code — AWS CDK (TypeScript) | Accepted |
| [ADR-006](#adr-006) | ORM and data access layer — Prisma | Accepted |
| [ADR-007](#adr-007) | Monorepo structure — single Git repo, independent workspaces | Accepted |
| [ADR-008](#adr-008) | Container platform — ECS Fargate (not EKS or EC2) | Accepted |
| [ADR-009](#adr-009) | Secret management — AWS Secrets Manager (not Parameter Store or env bake) | Accepted |
| [ADR-010](#adr-010) | CI/CD — GitHub Actions with OIDC federation (no long-lived AWS keys) | Accepted |

---

## ADR-001

### Title: Frontend framework — Next.js 14 App Router with React Server Components

**Status:** Accepted
**Date:** 2024-01-15
**Deciders:** Engineering lead, frontend team

---

### Intent

Choose a React rendering framework that meets the product's SEO, initial-load performance,
and authenticated-SSR requirements while remaining maintainable by a team with existing
React expertise.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-FE-001 | Authenticated pages must be server-rendered (SSR) — content cannot flash unauthenticated state |
| REQ-FE-002 | Public marketing / landing pages must be indexable by search engines |
| REQ-FE-003 | Core Web Vitals (LCP < 2.5 s, CLS < 0.1) must pass in production |
| REQ-FE-004 | Auth session must never be readable by browser JavaScript (XSS protection) |
| REQ-SEC-001 | Session cookie must be read server-side; tokens must not live in `localStorage` |

### Decision

Use **Next.js 14 with the App Router** and React Server Components (RSC) as the primary
rendering model. Server components fetch data and render HTML on the server; client
components are used only where browser APIs, interactivity, or client-side state are
required. Auth is gated in `middleware.ts` by reading the HTTP-only session cookie via the
Next.js `cookies()` helper.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| Vite SPA (React + React Router) | No SSR — fails REQ-FE-001, REQ-FE-002, REQ-SEC-001 without significant additional complexity (SSR adapters, etc.) |
| Next.js Pages Router | Superseded by App Router; no RSC support; larger client bundle; `getServerSideProps` boilerplate |
| Remix | Strong SSR story but smaller ecosystem; less team familiarity; form/mutation model differs; evaluated but not preferred |
| Astro | Excellent static story but thin React component support; not a good fit for a data-heavy authenticated app |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ RSC reduces client bundle | Data-fetching components never ship their dependencies to the browser |
| ✅ `cookies()` enables server-side auth | Session cookie is read before any client JS runs — no auth flash |
| ✅ Streaming and Suspense | Incremental HTML delivery improves perceived performance |
| ⚠️ RSC mental model is new | Team needs time to internalise server/client component boundary rules |
| ⚠️ `"use client"` boundary errors are subtle | Serialisation constraints on props crossing the server/client boundary need vigilance |
| ⚠️ Deployment requires a Node.js server | Static export is not possible for authenticated routes; ECS Fargate is required |

---

## ADR-002

### Title: Authentication transport — HTTP-only secure cookies (not bearer tokens)

**Status:** Accepted
**Date:** 2024-01-15
**Deciders:** Engineering lead, security review

---

### Intent

Choose an authentication credential transport that eliminates the primary XSS-based
credential theft vector and works correctly with server-side rendering.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-SEC-001 | Session tokens must not be accessible via `document.cookie` or `localStorage` |
| REQ-SEC-002 | CSRF risk must be mitigated without breaking the SSR data-fetch pattern |
| REQ-SEC-003 | Session revocation must be possible server-side immediately (no short-lived JWT grace period) |

### Decision

The backend issues **HTTP-only, Secure, SameSite=Lax session cookies**. The frontend
never writes to or reads `document.cookie`; the browser sends the cookie automatically on
same-site requests. Next.js server components and route handlers read the cookie via
`cookies()` from `next/headers` and forward it to the internal API. `localStorage` and
`sessionStorage` are not used for any credential.

CSRF is mitigated by `SameSite=Lax` combined with requiring `Content-Type:
application/json` (or `multipart/form-data`) on mutating endpoints — plain form-submit
CSRF attacks cannot set a custom `Content-Type` in cross-origin requests.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| Bearer token in `Authorization` header stored in `localStorage` | `localStorage` is readable by any same-origin JS; XSS gives full session access — fails REQ-SEC-001 |
| Short-lived JWT + refresh token in HttpOnly cookie | Added complexity; JWTs cannot be revoked until expiry without a blocklist; fails REQ-SEC-003 |
| `sessionStorage` bearer token | Not accessible after tab close / SSR; effectively browser-memory-only — incompatible with SSR data fetch |
| OAuth 2.0 PKCE flow (SPA flow) | Appropriate for third-party IdP; over-engineered for an internal session; tokens still need secure storage |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ XSS cannot steal the session token | Cookie is inaccessible to JavaScript at any time |
| ✅ Immediate server-side revocation | Session record deleted → cookie rejected on next request |
| ✅ Works seamlessly with SSR | `cookies()` gives server components access before the page renders |
| ⚠️ Requires HTTPS in all environments | Cookie `Secure` flag means HTTP-only local dev needs careful setup (or `Secure` flag omitted in dev only) |
| ⚠️ CORS configuration is more complex | Credentials mode must be explicit (`credentials: 'include'`) on client-side `fetch` calls |
| ⚠️ Multi-subdomain auth needs `COOKIE_DOMAIN` tuning | Must be set correctly per environment |

---

## ADR-003

### Title: Backend framework — dedicated Express API service (not Next.js Route Handlers only)

**Status:** Accepted
**Date:** 2024-01-16
**Deciders:** Engineering lead, backend team

---

### Intent

Decide whether the API layer should live entirely inside Next.js Route Handlers or as a
separate independently-deployable Node.js service.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-API-001 | API must be independently scalable from the frontend |
| REQ-API-002 | API must be consumable by future mobile or third-party clients (not just the Next.js frontend) |
| REQ-API-003 | Team has deep Express expertise and existing reusable middleware |

### Decision

The backend is a **dedicated Express 4 / Node.js service** deployed as its own ECS Fargate
task. It exposes a versioned REST API at `/api/v1/…`. The Next.js frontend communicates
with it over the internal VPC network via `API_INTERNAL_URL`. External browser-side fetch
calls also route to it via CloudFront → ALB path-based routing on `/api/*`.

Next.js Route Handlers are used only for thin server-side proxying, redirect logic, and
BFF patterns that are tightly coupled to the UI — not for business logic.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| All API in Next.js Route Handlers | Cannot scale independently; couples frontend and API deploy cycles; harder to version; does not satisfy REQ-API-002 |
| GraphQL (Apollo Server) | Over-engineered for a CRUD-heavy domain at this scale; adds client-side caching complexity; team has limited Apollo expertise |
| tRPC | Excellent DX for a TypeScript monorepo but couples frontend and backend build; less suitable for future non-TS consumers |
| NestJS | Solid choice but larger learning curve; Express is familiar and sufficient for current complexity |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Independent scaling | Frontend and API ECS services can scale to different task counts |
| ✅ Clear contract boundary | OpenAPI / generated TypeScript types enforce the contract; no implicit coupling |
| ✅ Future-proof | Mobile or third-party clients can consume `/api/v1/…` directly |
| ⚠️ Two services to maintain | Two Docker images, two ECS service definitions, two deploy targets |
| ⚠️ Network hop for SSR data | Server components call the internal API over HTTP; adds ~1–2 ms on the private VPC network (acceptable) |

---

## ADR-004

### Title: Database — Aurora PostgreSQL Serverless v2

**Status:** Accepted
**Date:** 2024-01-16
**Deciders:** Engineering lead, infrastructure team

---

### Intent

Choose a managed relational database that supports the application's data model, meets
durability and availability requirements, and is cost-effective across non-production and
production environments.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-DB-001 | ACID transactions required for multi-entity writes |
| REQ-DB-002 | Relational schema with foreign-key constraints and joins |
| REQ-DB-003 | Non-production environments should not incur idle database costs |
| REQ-DB-004 | Database must have no public endpoint (private subnet only) |
| REQ-INFRA-001 | All infrastructure must be on AWS |

### Decision

Use **Amazon Aurora PostgreSQL Serverless v2** (PostgreSQL 15 compatible). Serverless v2
scales ACUs (Aurora Capacity Units) down to 0.5 ACU in low-traffic environments and scales
up in sub-second increments. Production uses a minimum of 1 ACU and a read replica for
read-heavy workloads. The Prisma ORM communicates with Aurora over a standard PostgreSQL
wire protocol; no Aurora-specific driver is needed.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| RDS PostgreSQL (provisioned) | Higher minimum cost for non-production; requires manual scaling; no auto-pause |
| Aurora Serverless v1 | HTTP Data API only — not compatible with Prisma's standard connection pooling; cold-start latency higher |
| DynamoDB | No joins or ACID transactions; schema-less model conflicts with a relational domain model |
| PlanetScale (MySQL) | Not AWS-native; cross-provider dependency; MySQL syntax differences with Prisma |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Scales to near-zero in dev/staging | Reduces idle compute cost significantly |
| ✅ PostgreSQL-compatible | Standard Prisma + `pg` client; no vendor lock-in on the ORM layer |
| ✅ Automatic storage scaling | No manual volume resizing |
| ⚠️ Cold-start latency | First query after an idle period may take 1–5 s in low-traffic environments; mitigated by keeping min ACU ≥ 0.5 |
| ⚠️ Aurora-specific pricing model | ACU-based pricing can be hard to forecast; monitoring alerts are required |
| ⚠️ VPC-only access | Local development uses a Dockerised PostgreSQL 15 instance; production uses Aurora — minor schema parity risk managed by Prisma migrations |

---

## ADR-005

### Title: Infrastructure-as-Code — AWS CDK (TypeScript)

**Status:** Accepted
**Date:** 2024-01-17
**Deciders:** Engineering lead, infrastructure team

---

### Intent

Choose an IaC tool that allows the infrastructure to be declared, versioned, reviewed, and
deployed with the same rigour as application code, and that is idiomatic for a TypeScript
monorepo on AWS.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-INFRA-001 | All infrastructure must be on AWS |
| REQ-INFRA-002 | Infrastructure changes must be code-reviewed and version-controlled |
| REQ-INFRA-003 | IaC must be written in a language the team already knows |
| REQ-INFRA-004 | IaC must produce repeatable environment bootstrapping |

### Decision

Use **AWS CDK v2 (TypeScript)**. CDK synthesises to CloudFormation, which AWS natively
supports. The `infra/` package uses the same TypeScript toolchain and `tsconfig` conventions
as the rest of the monorepo. Constructs are typed; mis-configured resources are caught at
synth time rather than deploy time where possible.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| AWS CloudFormation (raw YAML/JSON) | Verbose; no abstraction or type safety; error messages are poor |
| Terraform / OpenTofu | Excellent but introduces HCL — a second language; requires separate state backend setup |
| Pulumi (TypeScript) | Viable alternative; less mature AWS L2 constructs; smaller community than CDK for AWS-specific patterns |
| AWS SAM | Optimised for serverless; not appropriate for an ECS-based architecture |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Same language as app code | No context-switching; application engineers can read and contribute to infra |
| ✅ High-level constructs (L2/L3) | Sensible defaults for VPC, ECS, ALB, etc. reduce boilerplate and encoding errors |
| ✅ Type safety catches misconfiguration early | `cdk synth` fails on type errors before any AWS API call |
| ⚠️ CDK abstraction leaks | L2 constructs sometimes hide important CloudFormation properties; escape hatches (`addPropertyOverride`) are occasionally needed |
| ⚠️ CloudFormation dependency | Underlying CloudFormation limits (500 resources/stack, deployment timeouts) still apply |
| ⚠️ Bootstrap required | `cdk bootstrap` must be run once per account/region before the first deploy |

---

## ADR-006

### Title: ORM and data access layer — Prisma

**Status:** Accepted
**Date:** 2024-01-17
**Deciders:** Backend team

---

### Intent

Choose a data access layer that provides type-safe queries derived from the database
schema, manages migrations reliably, and integrates cleanly with the TypeScript + Zod
validation stack.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-DB-005 | All database queries must be parameterised (SQL injection prevention) |
| REQ-BE-001 | Query result types must be inferred from the schema — no hand-written DTOs |
| REQ-BE-002 | Migration workflow must be trackable in Git and runnable in CI |

### Decision

Use **Prisma ORM** as the sole data access layer in the backend. The `schema.prisma` file
is the single source of truth for the data model. Prisma Client is regenerated on `npm
install` and whenever the schema changes. Zod schemas for API request validation are
derived from Prisma types using `zod-prisma-types` or hand-authored to match the generated
Prisma model shapes — no independent DTO drift.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| TypeORM | Decorator-heavy; less predictable migration behaviour; generated types less ergonomic than Prisma Client |
| Drizzle ORM | Promising but younger; less mature migration tooling at evaluation time |
| Knex.js (query builder) | No type safety without separate schema definitions; requires hand-writing DTOs |
| Raw `pg` queries | Maximum control but high boilerplate; no migration management; type safety requires manual mapping |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Type-safe queries inferred from schema | Refactoring a model field produces TypeScript errors at every call site |
| ✅ Parameterised queries by default | No string interpolation into SQL; injection is structurally prevented |
| ✅ Migration management in Git | `prisma/migrations/` is version-controlled; CI applies them in order |
| ⚠️ Prisma Client bundle size | The generated client is relatively large; acceptable for a server-side-only usage (never shipped to the browser) |
| ⚠️ Complex joins require raw SQL | Very complex analytical queries fall back to `$queryRaw` — still parameterised via tagged templates |
| ⚠️ Schema-first only | Schema must be updated before application code can use a new column — enforces discipline but adds a migration step |

---

## ADR-007

### Title: Monorepo structure — single Git repo, independent workspaces

**Status:** Accepted
**Date:** 2024-01-14
**Deciders:** Engineering lead

---

### Intent

Decide whether to host the frontend and backend in the same repository or in separate
repositories.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-DX-001 | A single PR should be able to change frontend and backend together for atomic feature work |
| REQ-DX-002 | Frontend and backend must be independently buildable and deployable |
| REQ-DX-003 | Shared types between frontend and backend must be kept in sync without a separate publish step |

### Decision

Use a **single Git monorepo** with two independent npm workspaces (`frontend/` and
`backend/`). Each workspace has its own `package.json`, `node_modules`, lockfile, build
output, and Docker image. There is no root-level `node_modules` hoisting. Shared types are
consumed through the generated API client (sourced from the backend's OpenAPI spec) rather
than a shared package — this avoids coupling the build systems.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| Separate repositories (polyrepo) | Harder to make atomic cross-cutting changes; diverging tooling versions; friction for a small team |
| Turborepo / Nx monorepo with shared packages | Worthwhile at larger scale; adds tooling complexity for a two-app repo at this stage; can be adopted later |
| Single Next.js project (API routes only) | Rejected in ADR-003 — API must scale and deploy independently |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Atomic cross-cutting PRs | Frontend and backend changes ship together; reviewers see full context |
| ✅ Single CI pipeline configuration | One `.github/workflows/` directory; shared lint/test matrix |
| ⚠️ No shared package | Types shared via generated client; requires regeneration after backend contract changes |
| ⚠️ Repo clone includes both apps | Developers working only on one app still clone everything — acceptable for current team size |

---

## ADR-008

### Title: Container platform — ECS Fargate (not EKS or EC2)

**Status:** Accepted
**Date:** 2024-01-18
**Deciders:** Infrastructure team, engineering lead

---

### Intent

Choose a container orchestration platform on AWS that provides production-grade
reliability without requiring the team to manage control-plane infrastructure or become
Kubernetes operators.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-INFRA-001 | All infrastructure must be on AWS |
| REQ-INFRA-005 | The team should not need to manage container orchestration infrastructure |
| REQ-INFRA-006 | Rolling deploys with zero downtime must be supported |
| REQ-SCALE-001 | The platform must support horizontal scaling of both frontend and backend services independently |

### Decision

Use **Amazon ECS with Fargate launch type**. ECS manages scheduling and orchestration;
Fargate manages the underlying compute — no EC2 instances or node groups to patch. Each
application (frontend, backend) is an independent ECS service with its own task definition,
auto-scaling policy, and health-check configuration. Rolling deploys are handled natively
by ECS.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| Amazon EKS | Kubernetes expertise required for day-2 operations; control plane cost; over-engineered for two services |
| ECS on EC2 | Must manage EC2 fleet patching and capacity; Fargate removes this operational burden |
| AWS App Runner | Simpler but fewer networking controls (VPC integration, private subnets, SG rules); less configurable for our security requirements |
| AWS Lambda (containerised) | Cold-start latency unacceptable for a server-rendered frontend; 15-minute execution limit unsuitable for a persistent Express server |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ No cluster node management | AWS manages Fargate compute patching and availability |
| ✅ Per-task CPU/memory billing | No idle EC2 cost; pay only for running tasks |
| ✅ Native ECS rolling deploys | Zero-downtime deploys with configurable `minimumHealthyPercent` / `maximumPercent` |
| ⚠️ Fargate startup latency | New tasks take ~30–60 s to start; scale-out events lag slightly behind traffic spikes; mitigated by scheduled scaling |
| ⚠️ ECS is AWS-proprietary | Workload is less portable than Kubernetes; acceptable given the AWS-only mandate |

---

## ADR-009

### Title: Secret management — AWS Secrets Manager (not Parameter Store or env bake)

**Status:** Accepted
**Date:** 2024-01-18
**Deciders:** Engineering lead, security review

---

### Intent

Define how runtime secrets (database passwords, session keys, third-party API keys) are
stored, distributed, and rotated without ever appearing in Docker images, CI logs, or
application config files.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-SEC-004 | No secret must appear in a Docker image layer, a CI log, or a committed file |
| REQ-SEC-005 | Secrets must be rotatable without redeploying application code |
| REQ-SEC-006 | Access to secrets must be audited and scoped to least privilege |

### Decision

All runtime secrets are stored in **AWS Secrets Manager**. ECS task definitions reference
secrets by ARN in the `secrets` block; ECS injects them as environment variables at task
startup using the task execution role. The task execution role is granted `secretsmanager:GetSecretValue`
only on the specific secret ARNs it needs (least privilege). Application code reads secrets
from environment variables — no SDK calls to Secrets Manager at runtime. Rotation is
handled by Secrets Manager rotation Lambdas (for database passwords) or manual rotation
with version staging for static secrets.

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| SSM Parameter Store (SecureString) | Cheaper but less feature-rich rotation; Secrets Manager preferred for credentials that benefit from automated rotation |
| Environment variables baked into Docker image | Secrets embedded in image layers — violates REQ-SEC-004; unacceptable |
| GitHub Actions secrets as ECS env vars | CI secrets are deployment-time values, not runtime values; conflating the two creates rotation and audit complexity |
| HashiCorp Vault | Not AWS-native; adds operational overhead; requires self-managed HA cluster |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ Secrets never in image layers or logs | ECS injects at task start; never `printenv`-visible in CI |
| ✅ Audit trail | Every `GetSecretValue` call is logged in CloudTrail |
| ✅ Rotation without redeploy | Secrets Manager rotation Lambdas can rotate credentials; ECS picks up new values on next task start or forced redeploy |
| ⚠️ Secrets Manager cost | ~$0.40/secret/month + API call charges — negligible at this scale |
| ⚠️ ECS task role must have correct IAM | Misconfigured IAM = task fails to start; caught in staging before production |

---

## ADR-010

### Title: CI/CD — GitHub Actions with OIDC federation (no long-lived AWS keys)

**Status:** Accepted
**Date:** 2024-01-19
**Deciders:** Engineering lead, security review

---

### Intent

Design a CI/CD pipeline that builds, tests, and deploys both applications to AWS without
storing long-lived AWS credentials in GitHub or any CI secret store.

### Requirements context

| Requirement | Detail |
|-------------|--------|
| REQ-SEC-007 | No long-lived AWS IAM access keys must exist for CI/CD |
| REQ-CI-001 | Every PR must run lint, type-check, tests, and a build check |
| REQ-CI-002 | Merge to `main` must automatically deploy to staging |
| REQ-CI-003 | Production deploy must be triggered by a version tag and must not require manual credential rotation |

### Decision

Use **GitHub Actions** as the CI/CD platform. AWS credentials are obtained via **OIDC
federation**: GitHub Actions assumes a scoped AWS IAM role using a short-lived OIDC token
— no `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets are stored in GitHub. The IAM
role trust policy restricts assumption to the specific GitHub org, repo, and branch/tag
ref. The role has least-privilege permissions: ECR push, ECS update-service, and
Secrets Manager read for deploy-time config only.

Pipeline stages:

| Trigger | Jobs |
|---------|------|
| PR opened / updated | `lint` → `type-check` → `test` → `build-check` (all in parallel per workspace) |
| Merge to `main` | `build-and-push` (ECR) → `deploy-staging` (ECS rolling update) |
| Push `v*` tag | `promote-to-production` (re-tag staging image → ECS production deploy) |

### Alternatives considered

| Option | Reason rejected |
|--------|----------------|
| Long-lived IAM access keys in GitHub Secrets | Violates REQ-SEC-007; keys cannot be automatically rotated; breach of GitHub gives permanent AWS access |
| AWS CodePipeline + CodeBuild | No OIDC concern (IAM roles natively), but GitHub integration is a paid add-on; team prefers GitHub-native workflows |
| CircleCI / Jenkins | Viable but introduces a third platform; OIDC support exists but is less documented than GitHub Actions |

### Trade-offs and consequences

| Trade-off | Detail |
|-----------|--------|
| ✅ No persistent AWS credentials in GitHub | OIDC tokens are short-lived (15 min); breach of CI does not give long-term AWS access |
| ✅ Automatic credential expiry | Tokens expire after the job completes; no rotation schedule required |
| ✅ CloudTrail audit | All AWS API calls from CI are attributed to the OIDC-assumed role and logged |
| ⚠️ OIDC trust policy must be correctly scoped | Over-broad trust (e.g., allowing any branch to assume the production deploy role) is a misconfiguration risk; mitigated by branch/tag ref conditions in the trust policy |
| ⚠️ GitHub is a trust boundary | GitHub Actions runner compromise → temporary AWS access within the role's permissions; mitigated by least-privilege role policy and short token lifetime |

---

## Design Notes (DSN-001 – DSN-009)

> Design Notes capture implementation-level choices within the boundaries set by the ADRs
> above. They are cross-referenced to architecture Section 2 (component model) and Section 6
> (security boundaries). They do not supersede ADRs; if a DSN reveals a need to revisit an
> ADR, a new ADR must be opened.

---

### DSN-001 — `middleware.ts` session-verification strategy

**Relates to:** ADR-001, ADR-002 | **Architecture ref:** §2 COMP-003, §6 security boundaries
**Status:** Accepted | **Date:** 2024-01-20

**Context:** `middleware.ts` runs on every request to the Next.js service. It must decide
quickly whether to pass through or redirect to `/login`, without introducing a per-request
round-trip to the backend for every static asset or public route.

**Decision:**
- Apply the middleware only to the path matcher `['/((?!_next/static|_next/image|favicon.ico|public).*)']`.
- Check for the presence and cryptographic validity of the session cookie using a lightweight
  HMAC verify (shared `SESSION_SECRET`) — no database call in middleware.
- A full session freshness check (`/api/v1/auth/me`) is deferred to the first server
  component data fetch on protected pages so that stale or revoked tokens are caught
  within the first RSC render, not at the edge.

**Consequences:** Session revocation is detectable within one page navigation (not
necessarily at the CDN edge). Acceptable per REQ-SEC-003 which requires server-side
revocation, not edge-level revocation.

---

### DSN-002 — API client generation from OpenAPI spec

**Relates to:** ADR-003, ADR-007 | **Architecture ref:** §2 COMP-003, COMP-006
**Status:** Accepted | **Date:** 2024-01-20

**Context:** The frontend must consume typed API responses without hand-duplicating backend
DTOs (a primary source of drift in past projects).

**Decision:**
- The backend Express service emits an OpenAPI 3.1 spec at `GET /api/v1/openapi.json` in
  non-production environments and as a static artifact during CI build.
- The frontend workspace runs `openapi-typescript` (via `npm run generate:types`) to
  produce `frontend/src/lib/api-types.gen.ts` from the spec.
- All frontend API calls use a thin `fetcher` wrapper typed against the generated types;
  no manual `interface` declarations for server-originated shapes.
- The CI pipeline fails if the generated file is stale (diff check on the generated file
  after regeneration).

**Consequences:** Breaking API changes are surfaced as TypeScript errors in the frontend
before merge. The generation step adds ~5 s to CI. The OpenAPI endpoint must be kept
accurate; ownership is the backend team's responsibility.

---

### DSN-003 — Prisma connection pooling in ECS

**Relates to:** ADR-004, ADR-006, ADR-008 | **Architecture ref:** §2 COMP-006, COMP-008
**Status:** Accepted | **Date:** 2024-01-21

**Context:** Aurora Serverless v2 has a per-instance connection limit. ECS Fargate can run
many concurrent tasks; naive one-connection-per-task Prisma usage could exhaust the
Aurora connection pool under scale-out.

**Decision:**
- Deploy **PgBouncer** as a sidecar container on the backend ECS task definition in
  `transaction` pooling mode.
- Prisma connects to `localhost:6432` (PgBouncer); PgBouncer maintains a fixed pool
  to Aurora (configurable `pool_size`, default 10 per task).
- `DATABASE_URL` in the ECS task points to the PgBouncer sidecar; no application-level
  change is required.
- For local development, direct connection to Dockerised PostgreSQL is used; PgBouncer
  is not required locally.

**Consequences:** Connection usage is bounded per task. PgBouncer adds a sidecar image
to maintain and a small latency overhead (~0.1 ms per transaction). Prisma interactive
transactions (`$transaction`) must use the `interactiveTransactions` flag — supported
in PgBouncer `session` mode; we use a `session`-mode fallback for transactions.

---

### DSN-004 — CloudFront cache-control strategy

**Relates to:** ADR-001, ADR-008 | **Architecture ref:** §2 COMP-002, COMP-005
**Status:** Accepted | **Date:** 2024-01-21

**Context:** CloudFront sits in front of both the Next.js frontend and the S3 static
asset bucket. Caching must be tuned to serve static assets aggressively while ensuring
authenticated page content is never served stale or to wrong users.

**Decision:**

| Path pattern | Cache behaviour | TTL |
|---|---|---|
| `/_next/static/*` | Cache at edge (immutable — content-hashed filenames) | 365 days |
| `/favicon.ico`, `/robots.txt`, `/sitemap.xml` | Cache at edge | 1 day |
| `/_next/image*` | Cache at edge (image optimisation) | 60 s (Next.js default) |
| `/api/*` | Pass-through — never cached | 0 |
| All other routes (SSR pages) | Pass-through — never cached at CloudFront; authenticated content must not be edge-cached | 0 |

- CloudFront origin request policy forwards `Cookie` and `Authorization` headers for
  non-static paths so the backend receives auth context.
- `Cache-Control: no-store` is set on all API and SSR responses by the application.

**Consequences:** Static assets benefit from full CDN caching. Dynamic pages always hit
the Next.js origin. `/_next/static/*` assets use hashed names so 365-day TTL is safe
(stale assets are unreachable after deploy).

---

### DSN-005 — Structured logging format

**Relates to:** ADR-010 | **Architecture ref:** §2 COMP-009
**Status:** Accepted | **Date:** 2024-01-22

**Context:** CloudWatch Logs Insights and X-Ray require consistent log structure to enable
filtering, alerting, and trace correlation. Both the frontend (Next.js) and backend
(Express) services must emit logs in compatible formats.

**Decision:**
- Both services log in **JSON (newline-delimited)** to `stdout`.
- Required fields on every log line:

  ```jsonc
  {
    "level": "info",          // debug | info | warn | error
    "ts": "2024-01-22T10:00:00.000Z",
    "service": "frontend",    // or "backend"
    "traceId": "abc123",      // X-Ray trace ID (propagated via header)
    "msg": "human-readable message",
    "...context": {}          // optional domain-specific fields
  }
  ```

- **Forbidden fields:** `password`, `sessionId`, `cookie`, `authorization`, `token`,
  `secret`, `creditCard`, `ssn` — any field whose name or value may contain a credential
  or PII. A lint-time ESLint rule (`no-restricted-syntax`) enforces this in-repo.
- The backend uses `pino` for structured logging; the frontend uses a thin wrapper around
  `console` that emits JSON in production and human-readable output in development.

**Consequences:** Logs are queryable in CloudWatch Logs Insights. No secrets or PII in
log output (enforced by both lint rule and pino serialiser `redact` config). Trace IDs
enable request correlation across the frontend and backend services.

---

### DSN-006 — Error response envelope

**Relates to:** ADR-003 | **Architecture ref:** §2 COMP-006
**Status:** Accepted | **Date:** 2024-01-22

**Context:** The frontend and any future API consumers need a predictable error shape.
Ad-hoc error responses (plain strings, varying JSON structures) cause brittle error-handling
code.

**Decision:**
All API error responses use a consistent envelope:

```jsonc
{
  "error": {
    "code": "VALIDATION_ERROR",    // machine-readable, ALL_CAPS_SNAKE
    "message": "Email is invalid", // human-readable, suitable for display
    "details": [                   // optional — present for validation errors
      { "field": "email", "message": "Must be a valid email address" }
    ],
    "requestId": "req_abc123"      // correlates to CloudWatch log trace
  }
}
```

- HTTP status codes are canonical: `400` validation, `401` unauthenticated, `403`
  forbidden, `404` not found, `409` conflict, `422` unprocessable, `500` server error.
- The `code` enum is defined in the OpenAPI spec and generated into the frontend types.
- `500` responses **never** include stack traces or internal error messages — only a
  generic `"INTERNAL_SERVER_ERROR"` code and the `requestId` for log correlation.
- The Express global error handler (`middleware/errorHandler.ts`) owns this contract.

**Consequences:** Frontend error-handling code is uniform. `requestId` enables support
staff to correlate user-reported errors to CloudWatch logs without exposing internals.

---

### DSN-007 — Database migration safety in ECS rolling deploy

**Relates to:** ADR-004, ADR-006, ADR-008 | **Architecture ref:** §2 COMP-006, COMP-008
**Status:** Accepted | **Date:** 2024-01-23

**Context:** ECS rolling deploys run new task versions alongside old ones during the
transition window. Prisma migrations that drop or rename columns will break old task
versions reading the old schema simultaneously.

**Decision:**
- Migrations must be **backward-compatible** for at least one full deploy cycle. The
  workflow is: (1) add new column as nullable, (2) deploy application code that writes
  both old and new columns, (3) run data migration, (4) deploy code that uses only the
  new column, (5) remove old column in a follow-up migration.
- Migrations are applied by a one-shot **ECS run-task** (`migrate-runner`) job that
  executes `prisma migrate deploy` against the production database before the main rolling
  deploy begins. The deploy job depends on this task completing successfully.
- `prisma migrate deploy` (not `migrate dev`) is used in production — never interactive.
- Migration run-task logs are captured in CloudWatch and the CI pipeline fails if the
  run-task exits non-zero.

**Consequences:** Adds a pre-deploy step to the pipeline (~30 s). Zero-downtime deploys
are safe for schema changes as long as the backward-compatibility convention is followed.
Violating the convention is a human process gap, not a technical enforcement — a
pre-commit hook that checks for `DROP COLUMN` / `RENAME COLUMN` in new migration files
is the primary guard.

---

### DSN-008 — Multi-tenant row isolation strategy

**Relates to:** ADR-004, ADR-006 | **Architecture ref:** §2 COMP-006, COMP-008
**Status:** Accepted | **Date:** 2024-01-23

**Context:** The application is multi-tenant. Every resource (projects, records, files)
belongs to a tenant. A data leak between tenants would be a critical security incident.

**Decision:**
- Every resource table carries a `tenantId` column (UUID, non-nullable, FK to `tenants`
  table, indexed).
- All Prisma queries in service-layer functions **must** include `where: { tenantId }` as
  a mandatory filter. A custom ESLint rule (`enforce-tenant-filter`) checks all Prisma
  `findMany`, `findFirst`, `update`, `delete`, and `upsert` calls for the presence of a
  `tenantId` filter on tables annotated with `@tenant`.
- The `tenantId` is extracted from the validated session (set by the auth middleware) —
  never from the request body or query parameters.
- Integration tests include explicit cross-tenant access attempt scenarios that must
  return `404` (not `403`, to avoid tenant enumeration).

**Consequences:** Tenant isolation is structurally enforced at the ORM layer and verified
by linting and tests. The lint rule will generate false positives on admin-only queries
that legitimately span tenants; those call sites are annotated with an inline eslint
disable comment and require a code-review sign-off from the security owner.

---

### DSN-009 — Image upload and S3 presigned URL flow

**Relates to:** ADR-003, ADR-005 | **Architecture ref:** §2 COMP-003, COMP-005, COMP-006
**Status:** Accepted | **Date:** 2024-01-24

**Context:** Users can upload files (profile images, document attachments). Files must not
pass through the Express API or Next.js service (memory/bandwidth cost); they must be
stored in S3 privately and served via CloudFront with access control.

**Decision:**
1. The frontend requests a presigned PUT URL from the backend: `POST /api/v1/uploads/presign`.
2. The backend validates the request (file type allow-list: `image/jpeg`, `image/png`,
   `image/webp`, `application/pdf`; max size: 10 MB enforced via `Content-Length-Range` in
   the presigned policy), generates a presigned S3 PUT URL valid for 5 minutes, and returns
   it with the final object key.
3. The frontend uploads directly from the browser to S3 using the presigned URL — the
   file never touches the application servers.
4. After upload completes, the frontend calls `POST /api/v1/uploads/confirm` with the
   object key; the backend verifies the object exists in S3 (via S3 `HeadObject`), records
   the reference in the database, and returns the CloudFront-served URL.
5. S3 objects are **private** (no public read ACL). CloudFront uses Origin Access Control
   (OAC). Signed CloudFront URLs are issued by the backend for time-limited access to
   private documents; public assets (profile images) use unsigned CloudFront URLs.

**Consequences:** Large file uploads do not saturate Express or Next.js memory. The
5-minute presigned URL window limits exposure if a URL is leaked. File-type validation on
the backend prevents polyglot/MIME-sniffing attacks (enforced by the `Content-Type`
condition on the S3 bucket policy in addition to the presigned policy). Direct S3 upload
means the backend never holds file bytes in memory.

---

## Decision Status Records (DEC-001 – DEC-006)

> The DEC table provides a rapid audit view of the current resolution status for all
> in-flight and recently resolved cross-cutting decisions. It cross-references the ADR or
> DSN where the full rationale lives.
>
> **Status values:**
> - `Accepted` — decision is final and implemented
> - `In Review` — decision is actively being debated; a PR or RFC is open
> - `Deferred` — decision is acknowledged but intentionally postponed with a stated
>   trigger/deadline
> - `Superseded` — replaced by a later decision; see the superseding reference
> - `Revoked` — reversed; no replacement; rationale recorded

---

| ID | Title | Status | Owner | Linked ADR/DSN | Last updated | Notes |
|----|-------|--------|-------|----------------|--------------|-------|
| [DEC-001](#dec-001) | Adopt `openapi-typescript` for frontend type generation | Accepted | Frontend lead | DSN-002, ADR-003 | 2024-01-20 | Replaces the earlier proposal to use a shared `types/` package |
| [DEC-002](#dec-002) | Use PgBouncer sidecar for connection pooling (not RDS Proxy) | Accepted | Backend lead | DSN-003, ADR-004 | 2024-01-21 | RDS Proxy evaluated and deferred — see DEC-002 notes |
| [DEC-003](#dec-003) | Defer Turborepo adoption to a future phase | Deferred | Engineering lead | ADR-007 | 2024-01-14 | Trigger: team grows beyond 5 engineers or build times exceed 5 min |
| [DEC-004](#dec-004) | Enforce tenant isolation via custom ESLint rule (not row-level security) | Accepted | Security owner | DSN-008, ADR-006 | 2024-01-23 | PostgreSQL RLS evaluated — see DEC-004 notes |
| [DEC-005](#dec-005) | Use CloudFront signed URLs for private document access (not S3 presigned GET) | Accepted | Backend lead | DSN-009, ADR-005 | 2024-01-24 | Provides longer TTL flexibility without re-issuing S3 credentials |
| [DEC-006](#dec-006) | Backward-compatible migration convention (no tooling enforcement yet) | In Review | Backend lead | DSN-007, ADR-006 | 2024-01-23 | Pre-commit hook for `DROP COLUMN`/`RENAME COLUMN` detection is planned — tracking in issue #42 |

---

### DEC-001

**Title:** Adopt `openapi-typescript` for frontend type generation
**Status:** Accepted
**Owner:** Frontend lead
**Date:** 2024-01-20
**Linked refs:** DSN-002, ADR-003

**Summary:** The earlier proposal to maintain a shared `packages/types` workspace was
rejected because it couples the frontend and backend build systems (violates ADR-007) and
requires a manual publish step. `openapi-typescript` generates types from the backend's
OpenAPI spec at build time, keeping the frontend contract in sync without a shared package.

**Acceptance criteria met:**
- [x] Generated types file (`frontend/src/lib/api-types.gen.ts`) is committed to the repo
  and updated in CI.
- [x] Frontend uses no manually-authored interfaces for server-originated shapes.
- [x] CI diff-check fails the build if the generated file is out of date.

---

### DEC-002

**Title:** Use PgBouncer sidecar for connection pooling (not RDS Proxy)
**Status:** Accepted
**Owner:** Backend lead
**Date:** 2024-01-21
**Linked refs:** DSN-003, ADR-004

**Summary:** AWS RDS Proxy was evaluated as an alternative to a PgBouncer sidecar. RDS
Proxy supports Aurora PostgreSQL and handles connection pooling at the AWS layer. It was
deferred for the following reasons:

- RDS Proxy requires IAM authentication or Secrets Manager credentials; the current Prisma
  setup uses a connection string — switching would require schema changes to the task
  definition and Secrets Manager.
- RDS Proxy costs approximately $0.015/vCPU-hour per database (in addition to the Aurora
  cost), which exceeds the PgBouncer sidecar cost at current scale.
- PgBouncer is well-understood by the team and the sidecar pattern is already established
  for other concerns.

RDS Proxy adoption is deferred to a future phase if connection pooling becomes a
bottleneck or the operational burden of managing the PgBouncer image becomes significant.

---

### DEC-003

**Title:** Defer Turborepo adoption
**Status:** Deferred
**Owner:** Engineering lead
**Date:** 2024-01-14
**Linked refs:** ADR-007

**Summary:** Turborepo or Nx would provide incremental build caching and parallel task
execution across workspaces. At current project scale (two workspaces, CI runs under
4 minutes), the tooling overhead is not justified.

**Trigger for revisit:** Team size exceeds 5 engineers, or CI wall-clock time (lint +
type-check + test + build across all workspaces) exceeds 5 minutes on a standard GitHub
Actions runner.

**Owner must revisit by:** Q3 2024

---

### DEC-004

**Title:** Enforce tenant isolation via custom ESLint rule (not PostgreSQL row-level security)
**Status:** Accepted
**Owner:** Security owner
**Date:** 2024-01-23
**Linked refs:** DSN-008, ADR-006

**Summary:** PostgreSQL row-level security (RLS) was evaluated as an alternative enforcement
mechanism for tenant isolation. RLS was not adopted for the following reasons:

- Prisma does not natively support setting a session-level PostgreSQL parameter (required
  for RLS policy variables) per query; workarounds involve raw SQL execution that breaks
  the type-safety benefits of ADR-006.
- RLS errors surface as database-level permission errors that are harder to translate into
  appropriate API error responses (403 vs. 404 — see DSN-008 on tenant enumeration).
- The custom ESLint rule (`enforce-tenant-filter`) catches missing `tenantId` filters at
  development time, not runtime — earlier feedback is preferable.

The ESLint rule enforcement is documented in DSN-008. The security owner reviews all
`eslint-disable` annotations on Prisma calls quarterly.

---

### DEC-005

**Title:** Use CloudFront signed URLs for private document access
**Status:** Accepted
**Owner:** Backend lead
**Date:** 2024-01-24
**Linked refs:** DSN-009, ADR-005

**Summary:** S3 presigned GET URLs were initially considered for serving private documents.
CloudFront signed URLs were chosen instead because:

- CloudFront signed URLs can be issued with longer TTLs (hours, not minutes) without
  re-exposing S3 credentials — relevant for document downloads where the user may need
  to resume a download.
- CloudFront signed URLs work with the existing OAC-only S3 bucket policy; S3 presigned
  GET URLs would require relaxing the OAC-only restriction.
- Geo-restriction, WAF, and access logging are applied at the CloudFront layer uniformly;
  S3 presigned URLs bypass CloudFront for those objects.

CloudFront key pairs are managed via CloudFront Key Groups; the private key is stored in
AWS Secrets Manager and injected into the backend ECS task at startup.

---

### DEC-006

**Title:** Backward-compatible migration convention (no tooling enforcement yet)
**Status:** In Review
**Owner:** Backend lead
**Date:** 2024-01-23
**Linked refs:** DSN-007, ADR-006

**Summary:** DSN-007 documents the required convention for backward-compatible migrations.
A pre-commit hook that detects `DROP COLUMN` and `RENAME COLUMN` statements in new
migration files has been designed but not yet implemented. Until the hook ships, the
convention is enforced by code review only.

**Open questions:**
- Should the hook also detect `NOT NULL` additions without a default (a common source of
  lock-table incidents)? *Proposed answer: yes — to be confirmed with the backend team.*
- Should violations block the commit (hard) or warn only (soft)? *Proposed: hard block
  with a `--no-verify` escape hatch.*

**Tracking issue:** [#42](../../issues/42) — *Implement migration safety pre-commit hook*

**Expected resolution:** End of current sprint (2024-02-09)

---

## Appendix: Requirements Summary

The table below cross-references all requirement IDs cited in the ADRs above.

| ID | Statement |
|----|-----------|
| REQ-FE-001 | Authenticated pages must be server-rendered — no unauthenticated flash |
| REQ-FE-002 | Public pages must be indexable (SEO) |
| REQ-FE-003 | Core Web Vitals must pass in production |
| REQ-FE-004 | Auth session must not be readable by browser JavaScript |
| REQ-SEC-001 | Session tokens must not be in `localStorage`; must use HTTP-only cookies |
| REQ-SEC-002 | CSRF risk must be mitigated |
| REQ-SEC-003 | Session revocation must be immediate (server-side) |
| REQ-SEC-004 | No secret in Docker image, CI log, or committed file |
| REQ-SEC-005 | Secrets must be rotatable without redeploying code |
| REQ-SEC-006 | Secret access must be audited and least-privilege |
| REQ-SEC-007 | No long-lived AWS IAM keys for CI/CD |
| REQ-API-001 | API must scale independently from the frontend |
| REQ-API-002 | API must be consumable by non-frontend clients (mobile, third-party) |
| REQ-API-003 | Team has Express expertise and reusable middleware |
| REQ-DB-001 | ACID transactions required |
| REQ-DB-002 | Relational schema with FK constraints and joins |
| REQ-DB-003 | Non-production databases must not incur idle cost |
| REQ-DB-004 | Database must have no public endpoint |
| REQ-DB-005 | All queries must be parameterised |
| REQ-BE-001 | Query result types must be inferred from schema |
| REQ-BE-002 | Migration workflow must be trackable in Git and runnable in CI |
| REQ-INFRA-001 | All infrastructure must be on AWS |
| REQ-INFRA-002 | Infrastructure changes must be code-reviewed and version-controlled |
| REQ-INFRA-003 | IaC must use a language the team already knows |
| REQ-INFRA-004 | IaC must produce repeatable environment bootstrapping |
| REQ-INFRA-005 | Team must not manage container orchestration infrastructure |
| REQ-INFRA-006 | Rolling zero-downtime deploys must be supported |
| REQ-SCALE-001 | Frontend and backend must be independently horizontally scalable |
| REQ-DX-001 | A single PR must support atomic frontend + backend changes |
| REQ-DX-002 | Frontend and backend must be independently buildable and deployable |
| REQ-DX-003 | Shared types must stay in sync without a separate publish step |
| REQ-CI-001 | Every PR must run lint, type-check, tests, and build check |
| REQ-CI-002 | Merge to `main` must auto-deploy to staging |
| REQ-CI-003 | Production deploy triggered by version tag; no manual credential rotation |
