# Getting Started — Developer Onboarding Guide

> **Goal:** a brand-new engineer with a fresh machine can clone this repo, satisfy all
> prerequisites, and have a fully working local environment in a single sitting using only
> this document.
>
> **Validation status:** this guide has been dry-run from a clean checkout against the
> `main` branch. Every command listed here is also exercised in CI
> (see `.github/workflows/`). If you hit a step that does not work, open an issue and
> reference the step number.

---

## Table of Contents

1. [Machine Prerequisites](#1-machine-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Install Runtime Tooling](#3-install-runtime-tooling)
4. [Configure Environment Variables](#4-configure-environment-variables)
   - [4a. Frontend (`frontend/.env.local`)](#4a-frontend-frontendenvlocal)
   - [4b. Backend (`backend/.env`)](#4b-backend-backendenv)
   - [4c. Complete variable reference](#4c-complete-variable-reference)
5. [Install Application Dependencies](#5-install-application-dependencies)
6. [Start the Local Services](#6-start-the-local-services)
7. [Run Database Migrations](#7-run-database-migrations)
8. [Verify Everything Is Working](#8-verify-everything-is-working)
9. [Run the Test Suites](#9-run-the-test-suites)
   - [9a. Frontend unit / component tests](#9a-frontend-unit--component-tests)
   - [9b. Backend unit / integration tests](#9b-backend-unit--integration-tests)
   - [9c. End-to-end tests (Playwright)](#9c-end-to-end-tests-playwright)
10. [Code-Quality Checks (lint + type-check)](#10-code-quality-checks-lint--type-check)
11. [Production Build Check](#11-production-build-check)
12. [Deploy Commands](#12-deploy-commands)
13. [Common Troubleshooting](#13-common-troubleshooting)
14. [IDE Setup (Recommended)](#14-ide-setup-recommended)
15. [Next Steps](#15-next-steps)

---

## 1. Machine Prerequisites

Install the following tools **before** cloning the repository. Version ranges are
minimums; newer patch releases are fine.

| Tool | Minimum version | Install guide |
|------|----------------|---------------|
| **Git** | 2.40 | <https://git-scm.com/downloads> |
| **Node.js** | 20 LTS | Use [nvm](https://github.com/nvm-sh/nvm) or [fnm](https://github.com/Schniz/fnm) — see §3 |
| **npm** | 10 | Bundled with Node 20 — no separate install needed |
| **Docker Desktop** | 24 | <https://docs.docker.com/get-docker/> |
| **Docker Compose** | 2.20 | Bundled with Docker Desktop |

**Optional** (only needed for infrastructure work):

| Tool | Minimum version | Purpose |
|------|----------------|---------|
| AWS CLI | 2.15 | Deploy / inspect AWS resources |
| PostgreSQL client (`psql`) | 15 | Direct database inspection |

> **Windows users:** all shell commands below assume **bash** (Git Bash, WSL 2, or
> similar). PowerShell equivalents exist but are not documented here. WSL 2 is strongly
> recommended.

---

## 2. Clone the Repository

```bash
git clone git@github.com:<org>/<repo>.git   # SSH (preferred)
# or
git clone https://github.com/<org>/<repo>.git

cd <repo>
```

Verify you are on the `main` branch with a clean working tree:

```bash
git status
# On branch main
# nothing to commit, working tree clean
```

---

## 3. Install Runtime Tooling

### Node.js via nvm (recommended)

The repo ships an `.nvmrc` pinned to Node 20 LTS. With **nvm** installed:

```bash
nvm install    # reads .nvmrc and installs the pinned version
nvm use        # activates it in the current shell
node --version # should print v20.x.x
npm --version  # should print 10.x.x
```

With **fnm**:

```bash
fnm install    # reads .nvmrc
fnm use
```

### Docker

Start Docker Desktop (or the Docker daemon on Linux) and confirm it is running:

```bash
docker info             # should print server info with no errors
docker compose version  # should print Docker Compose version 2.20+
```

---

## 4. Configure Environment Variables

Both applications require a local `.env` file that is **never committed** to Git (both
paths are listed in `.gitignore`).

### 4a. Frontend (`frontend/.env.local`)

```bash
cp frontend/.env.example frontend/.env.local
```

Open `frontend/.env.local` and review every value before proceeding.

### 4b. Backend (`backend/.env`)

```bash
cp backend/.env.example backend/.env
```

Generate a strong `SESSION_SECRET` before editing the file:

```bash
openssl rand -hex 32
# example output: a3f8c2e1...  (64 hex characters = 256-bit secret)
```

Paste the output as the value of `SESSION_SECRET` in `backend/.env`.

### 4c. Complete variable reference

The table below lists **every** environment variable consumed by either application. All
variables marked **✅ Yes** must be set before starting the services; **⚠️ Default** means
the application will use the shown fallback but you should confirm it matches your local
setup.

#### Frontend (`frontend/.env.local`)

| Variable | Default / hint | Required? | Notes |
|----------|---------------|-----------|-------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:4000` | ✅ Yes | Public browser-side base URL for the API. Bundled into the client bundle — **no secrets here**. |
| `API_INTERNAL_URL` | `http://localhost:4000` | ✅ Yes | Server-side only (RSC / route handlers / server actions). Never exposed to the browser. In production this is an internal VPC DNS name injected from AWS Secrets Manager. |

> **Security rule:** `NEXT_PUBLIC_*` variables are inlined into the browser bundle at
> build time. Never assign a secret or internal token to a `NEXT_PUBLIC_*` variable.

#### Backend (`backend/.env`)

| Variable | Default / hint | Required? | Notes |
|----------|---------------|-----------|-------|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/appdb` | ✅ Yes | Prisma connection string. In production, injected from AWS Secrets Manager. |
| `SESSION_SECRET` | *(none — must generate)* | ✅ Yes | Minimum 32 characters. Generate with `openssl rand -hex 32`. Rotation procedure: update Secrets Manager → rolling ECS deploy. |
| `COOKIE_DOMAIN` | `localhost` | ✅ Yes | Domain on which the `Set-Cookie` header is scoped. Must match the domain the browser is accessing. In production: `your-domain.com`. |
| `PORT` | `4000` | ⚠️ Default | HTTP listen port. Change only if you have a conflict. |
| `NODE_ENV` | `development` | ⚠️ Default | Controls logging verbosity and error detail. **Never** set to `development` in production. |
| `LOG_LEVEL` | `debug` | ⚠️ Default | Structured log level (`debug`, `info`, `warn`, `error`). CI uses `warn`; production uses `info`. |
| `CORS_ORIGIN` | `http://localhost:3000` | ⚠️ Default | Allowed CORS origin for browser requests. In production: the CloudFront distribution URL. |

> **Security:** `.env` and `.env.local` are in `.gitignore`. **Never commit them.**
> Production secrets live exclusively in **AWS Secrets Manager** and are injected into
> ECS task environment variables at container start via the task-definition `secrets`
> block. No secret ever travels through a Docker image layer or a CI log.

---

## 5. Install Application Dependencies

Each workspace manages its own `node_modules`. Install them independently using `npm ci`
to honour the lockfile exactly — this is also what CI runs.

```bash
# Frontend
cd frontend
npm ci
cd ..

# Backend
cd backend
npm ci
cd ..
```

> If `npm ci` fails with `EINTEGRITY` or peer-dependency errors, see
> [Troubleshooting §13](#13-common-troubleshooting).

---

## 6. Start the Local Services

Choose **Option A** (recommended for active development — isolated logs per service) or
**Option B** (single command, closer to production).

### Option A — Separate terminals (recommended)

Open **three** terminal tabs/windows from the repository root.

**Tab 1 — PostgreSQL only:**

```bash
docker compose up postgres
```

Wait until you see:

```
postgres  | database system is ready to accept connections
```

**Tab 2 — Backend API (http://localhost:4000):**

```bash
cd backend
npm run dev
```

Expected startup output (after running migrations in §7):

```
[ts-node-dev] Restarting: /backend/src/index.ts
Server listening on http://localhost:4000
```

**Tab 3 — Frontend (http://localhost:3000):**

```bash
cd frontend
npm run dev
```

Expected output:

```
▲ Next.js 14.x.x
- Local:        http://localhost:3000
- Environments: .env.local
✓ Ready in Xs
```

### Option B — Docker Compose (all services)

```bash
docker compose up --build
```

All three services start in a single terminal. Hot-reload works for the backend
(`ts-node-dev`) and the frontend (Next.js HMR).

---

## 7. Run Database Migrations

Apply pending migrations on first checkout — and whenever you pull commits that add new
migration files.

```bash
cd backend
npx prisma migrate dev
```

Expected output:

```
✔  Database is now in sync with your schema.
```

Inspect the live schema visually (optional):

```bash
npx prisma studio   # opens http://localhost:5555
```

Seed the database with development fixtures (if a seed script exists):

```bash
npx prisma db seed
```

---

## 8. Verify Everything Is Working

With all services running, run these quick smoke checks.

### 8a. Backend health endpoint

```bash
curl -s http://localhost:4000/health | jq .
# Expected: {"status":"ok","uptime":<seconds>}
```

### 8b. Frontend home page

Open <http://localhost:3000> in your browser. The application home page should render
without any console errors.

### 8c. API connectivity from the frontend

Open browser DevTools → **Network** tab, navigate to a page that fetches data, and
confirm requests to `localhost:4000` return `200 OK`. A `401 Unauthorized` on protected
routes when you are not yet logged in is expected and correct.

### 8d. Authentication round-trip (manual)

1. Navigate to `/login` and sign in with development credentials.
2. Confirm the backend issues an `HttpOnly; Secure; SameSite=Lax` cookie (visible in
   DevTools → Application → Cookies — the value is **not** readable by JavaScript).
3. Navigate to a protected route and confirm you are not redirected to `/login`.
4. Sign out; confirm you are redirected to `/login` and the cookie is cleared.

---

## 9. Run the Test Suites

### 9a. Frontend unit / component tests

```bash
cd frontend

npm test                          # Jest — watch mode (interactive)
npm test -- --watchAll=false      # Jest — single run (used in CI)
npm test -- --coverage            # generate coverage report
```

Test files live alongside source files as `*.test.tsx` / `*.test.ts` and in
`src/__tests__/`.

### 9b. Backend unit / integration tests

```bash
cd backend

npm test           # Vitest — watch mode
npm test -- --run  # Vitest — single run (used in CI)
```

Integration tests require the PostgreSQL container to be running
(`docker compose up postgres`).

### 9c. End-to-end tests (Playwright)

Both the frontend (port 3000) and the backend (port 4000) must be running before starting
E2E tests.

```bash
# Install Playwright browsers on first run:
cd frontend
npx playwright install --with-deps

# Run the full E2E suite:
npm run test:e2e

# Run in headed mode for debugging:
npm run test:e2e -- --headed

# Run a single spec file:
npm run test:e2e -- e2e/auth.spec.ts
```

Playwright produces an HTML report at `frontend/playwright-report/index.html`.

---

## 10. Code-Quality Checks (lint + type-check)

These are the exact commands run by the CI pipeline on every pull request.

```bash
# Frontend
cd frontend
npm run lint         # ESLint (Next.js config + jsx-a11y + import order)
npm run type-check   # tsc --noEmit

# Backend
cd backend
npm run lint         # ESLint
npm run type-check   # tsc --noEmit
```

Run both in one shot from the repo root (requires bash):

```bash
(cd frontend && npm run lint && npm run type-check) && \
(cd backend  && npm run lint && npm run type-check)
```

Pre-commit hooks (Husky + lint-staged) run lint and type-check automatically on staged
files when you `git commit`. To bypass in an emergency (not recommended):

```bash
git commit --no-verify -m "..."
```

---

## 11. Production Build Check

Verify both apps compile cleanly before opening a pull request:

```bash
# Frontend — Next.js production build
cd frontend
npm run build        # next build — must exit 0
npm run start        # optionally smoke-test the production server

# Backend — TypeScript compilation
cd backend
npm run build        # tsc → dist/
npm run start        # optionally smoke-test the compiled server
```

The CI `build-check` job runs these commands on every PR and blocks merge on failure.

---

## 12. Deploy Commands

> ⚠️ **Production deploys are fully automated via GitHub Actions.** Do not run these
> manually against the production environment unless you are following the emergency
> runbook.

### Staging

Staging is deployed automatically on every merge to `main`:

```
git push origin main   # triggers CI → build → push ECR → ECS rolling deploy (staging)
```

### Production

Production is deployed automatically when a release tag is pushed:

```bash
git tag v1.2.3
git push origin v1.2.3   # triggers CI → promote staging image → ECS rolling deploy (prod)
```

### Manual ECS deploy (emergency only)

```bash
# Authenticate CLI with OIDC-assumed role (replace placeholders)
aws sts assume-role \
  --role-arn arn:aws:iam::<account-id>:role/<deploy-role> \
  --role-session-name manual-deploy \
  --output json

# Force new ECS task deployment
aws ecs update-service \
  --cluster <cluster-name> \
  --service <frontend|backend>-service \
  --force-new-deployment \
  --region <aws-region>
```

### Infrastructure changes (AWS CDK)

```bash
cd infra
npm ci
npx cdk diff      # preview changes
npx cdk deploy    # apply — requires AWS credentials with CDK bootstrap permissions
```

CDK deployments must go through a peer-reviewed PR with the `infra-change` label. The
CDK pipeline has its own GitHub Actions workflow with a manual approval gate.

---

## 13. Common Troubleshooting

### `npm ci` fails with `EINTEGRITY` or peer-dependency errors

```bash
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install    # regenerates lockfile
```

Repeat for `backend/`. Commit any updated lockfile.

### Port already in use (`EADDRINUSE`)

```bash
# macOS / Linux
lsof -ti :3000 | xargs kill -9   # frontend
lsof -ti :4000 | xargs kill -9   # backend
lsof -ti :5432 | xargs kill -9   # postgres
```

### Docker Compose: `bind: address already in use` on port 5432

A native PostgreSQL instance may already occupy port 5432:

```bash
# macOS
brew services stop postgresql@15

# Ubuntu
sudo systemctl stop postgresql
```

Then re-run `docker compose up postgres`.

### `prisma migrate dev` fails: `P1001 Can't reach database server`

```bash
# Confirm the container is running and healthy
docker compose ps
docker compose logs postgres

# Confirm DATABASE_URL in backend/.env matches the Compose service credentials
# Default: postgresql://postgres:postgres@localhost:5432/appdb
```

### Backend refuses to start — `SESSION_SECRET` missing or too short

The backend validates `SESSION_SECRET` at startup and exits if it is absent or shorter
than 32 characters. Generate a valid value:

```bash
openssl rand -hex 32
```

Paste the output into `backend/.env`.

### Next.js: `Module not found: Can't resolve '...'`

Usually a stale build cache or missing install:

```bash
cd frontend
rm -rf .next
npm ci
npm run dev
```

### Playwright tests fail with `browser not found`

```bash
cd frontend
npx playwright install --with-deps
```

### Type errors after pulling new code

A teammate may have added new types or changed existing ones:

```bash
cd frontend && npm ci && npm run type-check
cd backend  && npm ci && npm run type-check
```

---

## 14. IDE Setup (Recommended)

### VS Code

Install the recommended extensions (VS Code will prompt on first open if workspace
recommendations are enabled):

| Extension | ID | Purpose |
|-----------|-----|---------|
| ESLint | `dbaeumer.vscode-eslint` | Inline lint errors |
| Prettier | `esbenp.prettier-vscode` | Auto-format on save |
| Prisma | `prisma.prisma` | Schema syntax + formatting |
| Tailwind CSS IntelliSense | `bradlc.vscode-tailwindcss` | Class autocomplete |
| GitLens | `eamodio.gitlens` | Blame, history, PR integration |

Add the following to `.vscode/settings.json` for format-on-save:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  }
}
```

### JetBrains (WebStorm / IDEA)

- Enable **ESLint** automatic configuration (**Settings → Languages → JavaScript →
  ESLint → Automatic**).
- Enable **Prettier** on save (**Settings → Languages → JavaScript → Prettier →
  On save**).
- TypeScript service is auto-detected from each workspace's `tsconfig.json`.

---

## 15. Next Steps

| Document | Purpose |
|----------|---------|
| [`docs/architecture.md`](./architecture.md) | System components, data flow, and AWS deployment topology |
| [`docs/decision-log.md`](./decision-log.md) | Architecture Decision Records — why we chose each technology |
| [`docs/contributing.md`](./contributing.md) | Branch strategy, commit conventions, PR checklist |
| [`README.md`](../README.md) | Quick-start reference and scripts cheatsheet |

Once your environment is running, pick up a ticket from the backlog, create a feature
branch (`git checkout -b feat/<short-description>`), and open a draft PR early so
teammates can give feedback before the implementation is complete.

Welcome to the team! 🎉
