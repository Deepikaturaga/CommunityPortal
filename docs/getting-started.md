# Getting Started

## Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| [Python](https://www.python.org/downloads/) | 3.12 | Backend runtime |
| [Poetry](https://python-poetry.org/docs/) | 1.8+ | Python dependency management (or use pip with the setuptools build backend) |
| [Node.js](https://nodejs.org/) | 20 LTS | Frontend toolchain |
| [npm](https://www.npmjs.com/) | 10+ | Frontend package manager (bundled with Node 20) |
| [Docker](https://docs.docker.com/get-docker/) | 24+ | Container builds and local compose |
| [Docker Compose](https://docs.docker.com/compose/) | 2.x | Local multi-service orchestration |
| [OpenTofu](https://opentofu.org/docs/intro/install/) | 1.7+ | Infrastructure as Code (Terraform-compatible) |
| [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html) | 2.x | AWS interaction and ECR login |
| AWS account | — | With permissions for VPC, ECS, Aurora, ElastiCache, S3, OpenSearch, SES, SQS, EventBridge, Secrets Manager, ECR, CloudWatch, WAF, IAM |

---

## Local Development Setup

### Backend (Python / FastAPI)

```bash
# 1. Clone the repository
git clone <repo-url>   # replace with actual URL when available
cd project-root

# 2. Install Python dependencies
cd backend
pip install -e ".[dev]"
# or, if using Poetry:
# poetry install

# 3. Configure local environment variables
cp .env.example .env
# Edit backend/.env — see the Environment Variables table below

# 4. Start local backing services (Postgres, Redis) via Docker Compose
# (docker-compose.yml at repository root — TBD)
docker compose up -d postgres redis

# 5. Run database migrations (Alembic)
# Uses DATABASE_SYNC_URL from the environment
cd backend
alembic upgrade head

# 6. Start the API in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`.

### Frontend (React / Vite)

```bash
# From the repository root
cd frontend

# Install dependencies
npm install

# Start the development server (proxies API calls to localhost:8000)
npm run dev
```

The frontend will be available at `http://localhost:5173` (default Vite port).

---

## Environment Variables

The following variables are the **only** ones actually referenced in the generated code.
Copy the template for your target environment and fill in values:

```bash
cp .env.example .env            # local development
cp .env.beta.example .env       # beta (pre-production)
cp .env.prod.example .env       # prod (production)
```

In deployed environments (beta / prod), **secret values are injected by AWS ECS from Secrets Manager** — do not commit real values to any file.

### Backend variables (`backend/.env`)

| Variable | Description | Example (local) | Required |
|----------|-------------|-----------------|----------|
| `DATABASE_URL` | Async SQLAlchemy DSN (asyncpg driver) used by the application | `postgresql+asyncpg://user:CHANGE_ME@localhost:5432/appdb` | Yes |
| `DATABASE_SYNC_URL` | Synchronous DSN used by Alembic migrations | `postgresql+psycopg2://user:CHANGE_ME@localhost:5432/appdb` | Yes (migrations) |
| `SECRET_KEY` | HMAC key for token signing — ≥32 bytes high-entropy random string | `CHANGE_ME_generate_a_real_random_secret_key` | Yes |
| `ENVIRONMENT` | Runtime environment tag (`development` / `beta` / `production`) | `development` | Yes |
| `COOKIE_SECURE` | Set `true` when behind HTTPS proxy (ALB in deployed envs) | `false` | No |
| `AWS_REGION` | AWS region for SDK calls (SES, SQS, EventBridge, S3) | `us-east-1` | Yes (AWS features) |
| `AWS_DEFAULT_REGION` | Fallback AWS region used by some SDK paths | `us-east-1` | No |
| `EVENT_BUS_NAME` | EventBridge custom bus name for content-lifecycle events | `app-events-local` | Yes (events) |
| `EVENTS_ENABLED` | Feature flag — set `false` to disable EventBridge locally | `false` | No |

### Session store / identity variables (`backend/.env`)

| Variable | Description | Example (local) | Required |
|----------|-------------|-----------------|----------|
| `REDIS_URL` | Redis DSN for session store and rate-limit counters | `redis://localhost:6379/0` | Yes |
| `REDIS_MAX_CONNECTIONS` | Redis connection pool size | `20` | No |
| `REDIS_SOCKET_TIMEOUT` | Redis socket timeout (seconds) | `2.0` | No |
| `REDIS_SOCKET_CONNECT_TIMEOUT` | Redis connect timeout (seconds) | `2.0` | No |
| `REDIS_SESSION_PREFIX` | Key prefix for session entries | `session:` | No |
| `SESSION_COOKIE_NAME` | Name of the session cookie issued to clients | `sid` | No |
| `SESSION_COOKIE_MAX_AGE` | Session cookie TTL in seconds | `3600` | No |
| `SESSION_COOKIE_SECURE` | Sets the `Secure` attribute (`true` in deployed envs) | `true` | No |
| `SESSION_COOKIE_HTTPONLY` | Sets `HttpOnly` attribute | `true` | No |
| `SESSION_COOKIE_SAMESITE` | SameSite policy (`lax` or `strict`) | `lax` | No |
| `SESSION_COOKIE_PATH` | Cookie path | `/` | No |
| `SESSION_SIGNING_SECRET` | Shared secret for signing session cookies — ≥32 bytes | `change-me-before-production-32b!` | Yes |

### Security header variables (`backend/.env`)

| Variable | Description | Example (local) | Required |
|----------|-------------|-----------------|----------|
| `HTTPS_BEHIND_PROXY` | Trust `X-Forwarded-Proto` from ALB; emit HSTS | `true` | No |
| `HSTS_MAX_AGE` | HSTS `max-age` in seconds | `31536000` | No |
| `HSTS_INCLUDE_SUBDOMAINS` | Include subdomains in HSTS | `true` | No |
| `HSTS_PRELOAD` | HSTS preload directive | `false` | No |
| `CORS_ALLOW_ORIGINS` | Comma-separated allowed CORS origins | `https://app.example.com` | Yes |
| `CORS_ALLOW_CREDENTIALS` | Allow cookies in cross-origin requests | `true` | No |
| `CORS_ALLOW_METHODS` | Allowed HTTP methods | `GET,POST,PUT,PATCH,DELETE,OPTIONS` | No |
| `CORS_ALLOW_HEADERS` | Allowed request headers | `Authorization,Content-Type,X-Request-ID` | No |
| `CSP_POLICY` | Full Content-Security-Policy header value | `default-src 'none'; frame-ancestors 'none'` | No |

### Test-only variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `TEST_DATABASE_URL` | DSN for the isolated test database | `postgresql+asyncpg://user:pw@localhost:5432/testdb` | Tests only |
| `AUTH_STUB_ENABLED` | Bypass real auth in integration tests | `true` | Tests only |
| `DYNAMODB_ENDPOINT_URL` | LocalStack/DynamoDB local endpoint for tests | `http://localhost:8000` | Tests only |
| `DYNAMODB_TABLE_NAME` | DynamoDB table name used in tests | `discussion-local` | Tests only |
| `DISCUSSION_TABLE_NAME` | Discussion service DynamoDB table | `discussion-local` | Tests only |
| `DISCUSSION_TTL_SECONDS` | TTL for discussion entries | `86400` | Tests only |

### Frontend variables (`frontend/.env`)

| Variable | Description | Example (local) | Required |
|----------|-------------|-----------------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL for the discussion API client | `http://localhost:8000` | Yes |
| `NEXT_PUBLIC_API_URL` | Base URL for the KB / general API client | `http://localhost:8000` | Yes |
| `BASE_URL` | Base URL used by Playwright E2E tests | `http://localhost:5173` | Tests only |
| `CI` | Set automatically by GitHub Actions; affects Playwright config | _(auto-set in CI)_ | CI only |
| `TEST_USER_EMAIL` | Email of the test account used in a11y/auth setup | `testuser@example.com` | a11y tests |
| `TEST_USER_PASSWORD` | Password of the test account | `CHANGE_ME_test_password` | a11y tests |

> **Security note:** `SECRET_KEY` and `SESSION_SIGNING_SECRET` must be high-entropy random strings (≥ 32 bytes) in all deployed environments. They are injected by AWS ECS from Secrets Manager at task launch time — never from committed files. The session cookie is issued with `HttpOnly`, `Secure`, and `SameSite=Lax/Strict` attributes (TASK-014).

---

## Environment Configuration Matrix (beta vs prod)

Environment-specific values differ primarily in AWS resource identifiers and feature flags. Secrets are always from AWS Secrets Manager in deployed environments.

| Variable | local | beta | prod |
|----------|-------|------|------|
| `ENVIRONMENT` | `development` | `beta` | `production` |
| `DATABASE_URL` | `postgresql+asyncpg://…@localhost/appdb` | _(Secrets Manager — Aurora beta)_ | _(Secrets Manager — Aurora prod)_ |
| `DATABASE_SYNC_URL` | `postgresql+psycopg2://…@localhost/appdb` | _(Secrets Manager — Aurora beta sync)_ | _(Secrets Manager — Aurora prod sync)_ |
| `SECRET_KEY` | `change-me-local…` | _(Secrets Manager)_ | _(Secrets Manager)_ |
| `SESSION_SIGNING_SECRET` | `change-me-before-production-32b!` | _(Secrets Manager)_ | _(Secrets Manager)_ |
| `REDIS_URL` | `redis://localhost:6379/0` | `rediss://beta-redis.…:6379` | `rediss://prod-redis.…:6379` |
| `SESSION_COOKIE_SECURE` | `false` | `true` | `true` |
| `COOKIE_SECURE` | `false` | `true` | `true` |
| `HTTPS_BEHIND_PROXY` | `false` | `true` | `true` |
| `AWS_REGION` | `us-east-1` | `us-east-1` | `us-east-1` |
| `EVENT_BUS_NAME` | `app-events-local` | `app-events-beta` | `app-events-prod` |
| `EVENTS_ENABLED` | `false` | `true` | `true` |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | `https://beta.app.example.com` | `https://app.example.com` |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | `https://api.beta.example.com` | `https://api.example.com` |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | `https://api.beta.example.com` | `https://api.example.com` |

---

## Running Tests

### Backend tests (pytest)

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test module
pytest tests/test_login_service.py -v

# Run the full identity suite (VER-001, VER-005–008)
pytest tests/identity/ tests/test_register.py tests/test_login_service.py -v

# Run authorization matrix (VER-004)
pytest tests/profile_admin/ -v

# Run discussion/moderation suite (VER-002)
pytest tests/test_moderation.py tests/routers/ -v

# Run post-service suite (VER-002, VER-010)
pytest tests/posts/ -v

# Run KB suite (VER-002, VER-004)
pytest tests/test_kb_articles.py tests/services/kb/ -v

# Run search suite including injection and visibility-leakage tests (VER-003)
pytest tests/search/ -v

# Run security tests — IaC scanner, log audit, pipeline gates (VER-018, VER-019)
pytest tests/security/ -v

# Run E2E journey tests (JRN-001–003 — requires running API)
pytest tests/e2e/ -v

# Run CSRF and security header tests (VER-013, VER-014)
pytest tests/test_csrf_middleware.py tests/test_http_headers.py tests/test_security_headers.py -v
```

### Frontend tests (Vitest + Playwright)

```bash
cd frontend

# Run unit/component tests with Vitest
npm test

# Watch mode
npm run test:watch

# Run Storybook accessibility scan
npm run test:a11y

# Run Playwright accessibility tests (requires running frontend + API)
npx playwright test tests/a11y/

# Type-check
npm run typecheck

# Lint
npm run lint
```

---

## Deployment

### Run Locally

```bash
# Start local Postgres and Redis via Docker Compose
docker compose up -d

# Run Alembic migrations
cd backend && alembic upgrade head

# Start API (from backend/)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (from frontend/)
npm run dev
```

### Deploy to AWS

#### Prerequisites

1. AWS CLI configured with credentials for the target account:
   ```bash
   aws configure          # or: aws sso login
   ```
2. OpenTofu installed (`tofu --version`).
3. Docker daemon running (for image builds and pushes).
4. ECR repositories created (provisioned by the first IaC apply).

---

#### Beta Environment

```bash
# 1. Configure AWS credentials for the beta account
aws sso login    # or: aws configure --profile beta

# 2. Navigate to the beta IaC environment
cd infra/envs/beta

# 3. Initialise OpenTofu (first time or after provider upgrades)
tofu init

# 4. Review the plan
# Provisions:
#   infra/network/       → VPC, subnets, route tables (TASK-001)
#   infra/iam/           → ECS task roles, execution roles (TASK-002)
#   infra/data/aurora    → Aurora cluster, KMS encryption (TASK-010)
#   infra/data/elasticache → Redis replication group (TASK-011)
#   infra/observability/ → CloudWatch log groups + X-Ray (TASK-005)
#   infra/waf/           → WAF with OWASP managed rules (TASK-006)
#   infra/edge/          → ALB, TLS termination (TASK-007)
tofu plan -var-file="beta.tfvars"

# 5. Apply infrastructure
tofu apply -var-file="beta.tfvars"

# 6. Build and push the backend image to ECR (beta)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS \
    --password-stdin <beta-account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t app-api backend/
docker tag app-api:latest \
  <beta-account-id>.dkr.ecr.us-east-1.amazonaws.com/app-api:latest
docker push \
  <beta-account-id>.dkr.ecr.us-east-1.amazonaws.com/app-api:latest

# 7. Run Alembic migrations against the beta Aurora cluster
# (typically run as an ECS one-off task or via the CI pipeline)
# DATABASE_SYNC_URL is injected from Secrets Manager in the task definition

# 8. Force a new ECS deployment to pick up the latest image
aws ecs update-service \
  --cluster app-beta \
  --service api-service \
  --force-new-deployment \
  --region us-east-1

# 9. Wait for tasks to stabilise
aws ecs wait services-stable \
  --cluster app-beta \
  --services api-service \
  --region us-east-1
```

---

#### Prod Environment

```bash
# 1. Configure AWS credentials for the prod account (elevated / break-glass role)
aws sso login --profile prod

# 2. Navigate to the prod IaC environment
cd infra/envs/prod

# 3. Initialise
tofu init

# 4. Review the plan — mandatory before apply in prod (TASK-004 gate)
tofu plan -var-file="prod.tfvars"

# 5. Apply — requires reviewed plan and elevated-role approval
tofu apply -var-file="prod.tfvars"

# 6. Build and push the backend image to ECR (prod)
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS \
    --password-stdin <prod-account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t app-api backend/
docker tag app-api:latest \
  <prod-account-id>.dkr.ecr.us-east-1.amazonaws.com/app-api:latest
docker push \
  <prod-account-id>.dkr.ecr.us-east-1.amazonaws.com/app-api:latest

# 7. Run migrations against Aurora prod (ECS one-off task)

# 8. Force ECS deployment
aws ecs update-service \
  --cluster app-prod \
  --service api-service \
  --force-new-deployment \
  --region us-east-1

aws ecs wait services-stable \
  --cluster app-prod \
  --services api-service \
  --region us-east-1
```

> **Security reminder:** Prod deployments must go through the CI/CD pipeline (TASK-003) with gated approvals and a reviewed IaC plan (TASK-004). Direct `tofu apply` from a developer workstation to prod is discouraged and requires break-glass access.

---

### CI/CD Pipeline Gates (TASK-003)

The GitHub Actions workflows in `.github/workflows/` enforce the following before any merge:

| Workflow | Gate | Blocks On |
|----------|------|-----------|
| `ci.yml` | Unit + integration tests | Any failure |
| `ci.yml` | Ruff lint + mypy type-check (backend) | Any error |
| `ci.yml` | ESLint + tsc (frontend) | Any error |
| `security-gates.yml` | SCA (`pip-audit`) | Critical/High CVE (VER-015) |
| `security-gates.yml` | Secret scanning (`.secrets.baseline`) | Any detected secret |
| `identity-tests.yml` | Full identity/session test suite | VER-001, VER-005–008 failures |
| `phase-024-discussion-tests.yml` | Discussion/moderation test suite | VER-002 failures |
| `frontend-tests.yml` | Frontend Vitest + a11y scan | Test/lint failures |

### Post-Deployment Verification Checklist

After each environment deploy, confirm the following before marking it complete:

- [ ] ECS services stable: `aws ecs wait services-stable …`
- [ ] API health check: `curl -sI https://<alb-endpoint>/health` returns 200
- [ ] Security headers present: `curl -sI … | grep -E "Strict-Transport-Security|Content-Security-Policy|X-Frame-Options"`
- [ ] CloudWatch log groups `/app/api` receiving structured JSON logs with `correlationId` (VER-019)
- [ ] Session cookie attributes: `HttpOnly; Secure; SameSite` (VER-007)
- [ ] CSRF token rejected on a state-changing request without token (VER-014)
- [ ] No hardcoded secrets in IaC scan (`backend/tests/security/test_iac_scanner.py` passes)

### Smoke Tests After First Deploy

```bash
# 1. API reachable through WAF/ALB
curl -sI https://<alb-endpoint>/health | grep "200"

# 2. Security headers
curl -sI https://<alb-endpoint>/health \
  | grep -E "Strict-Transport-Security|Content-Security-Policy|X-Frame-Options"

# 3. Structured logs flowing in CloudWatch
aws logs filter-log-events \
  --log-group-name /app/api \
  --filter-pattern "{ $.correlationId = \"*\" }" \
  --max-items 1 \
  --region us-east-1
```

---

> See [Architecture](./architecture.md) for service topology. See [Decision Log](./decision-log.md) for open decisions (DEC-001–DEC-006) that affect production provisioning.
