# Project Monorepo

> Full-stack web application with a **Next.js** frontend and a **Node.js/Express** backend, deployed on AWS.

---

## Table of Contents

1. [Overview](#overview)
2. [Repository Structure](#repository-structure)
3. [Tech Stack](#tech-stack)
4. [Prerequisites](#prerequisites)
5. [Getting Started](#getting-started)
   - [Environment Variables](#environment-variables)
   - [Install Dependencies](#install-dependencies)
   - [Run in Development](#run-in-development)
   - [Run with Docker Compose](#run-with-docker-compose)
6. [Available Scripts](#available-scripts)
7. [Testing](#testing)
8. [Code Quality](#code-quality)
9. [Deployment](#deployment)
10. [Contributing](#contributing)
11. [License](#license)

---

## Overview

This monorepo contains two sibling applications that share a single Git history and a common CI/CD pipeline:

| App | Path | Description |
|-----|------|-------------|
| **Frontend** | `frontend/` | Next.js 14 App Router — SSR/RSC, TypeScript, Tailwind CSS |
| **Backend** | `backend/` | Node.js / Express REST API — TypeScript, Prisma ORM, PostgreSQL |

Supporting infrastructure lives under `infra/` (AWS CDK / Terraform), CI workflows under `.github/workflows/`, and shared project documentation under `docs/`.

---

## Repository Structure

```
.
├── .github/
│   └── workflows/          # CI/CD pipeline definitions
├── docs/
│   ├── architecture.md     # System architecture overview
│   ├── getting-started.md  # Detailed developer onboarding guide
│   ├── decision-log.md     # Architecture Decision Records (ADRs)
│   └── contributing.md     # Contribution guidelines
├── frontend/               # Next.js web application
│   ├── public/             # Static assets
│   ├── src/
│   │   ├── app/            # App Router pages, layouts, route handlers
│   │   ├── components/     # Shared UI components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── lib/            # API client, utilities, generated types
│   │   └── styles/         # Global CSS / Tailwind config
│   ├── .env.example
│   ├── next.config.js
│   ├── package.json
│   └── tsconfig.json
├── backend/                # Express REST API
│   ├── prisma/             # Prisma schema and migrations
│   ├── src/
│   │   ├── controllers/    # Route controllers
│   │   ├── middleware/     # Auth, validation, error-handling middleware
│   │   ├── routes/         # Express router definitions
│   │   ├── services/       # Business logic layer
│   │   └── utils/          # Shared utilities
│   ├── .env.example
│   ├── package.json
│   └── tsconfig.json
├── infra/                  # AWS CDK / Terraform infrastructure-as-code
├── docker-compose.yml      # Local multi-service development environment
├── .gitignore
└── README.md               # ← you are here
```

---

## Tech Stack

### Frontend

| Layer | Technology |
|-------|-----------|
| Framework | [Next.js 14](https://nextjs.org/) (App Router, React Server Components) |
| Language | TypeScript 5 (strict mode) |
| Styling | [Tailwind CSS](https://tailwindcss.com/) |
| State / Data fetching | React built-ins + `fetch` in RSC; `@tanstack/react-query` for client-side |
| Auth | HTTP-only secure cookies (read server-side via `cookies()`) |
| Testing | [Jest](https://jestjs.io/) + [React Testing Library](https://testing-library.com/) + [Playwright](https://playwright.dev/) |
| Linting / Formatting | ESLint (Next.js config) + Prettier |

### Backend

| Layer | Technology |
|-------|-----------|
| Runtime | Node.js 20 LTS |
| Framework | [Express](https://expressjs.com/) 4 |
| Language | TypeScript 5 (strict mode) |
| ORM | [Prisma](https://www.prisma.io/) |
| Database | PostgreSQL 15 |
| Auth | Session cookies (HTTP-only, Secure, SameSite=Lax) |
| Validation | [Zod](https://zod.dev/) |
| Testing | [Vitest](https://vitest.dev/) + [Supertest](https://github.com/ladjs/supertest) |
| Linting / Formatting | ESLint + Prettier |

### Infrastructure & Tooling

| Concern | Technology |
|---------|-----------|
| Cloud provider | AWS (ECS Fargate, RDS Aurora, CloudFront, S3, Secrets Manager) |
| IaC | AWS CDK (TypeScript) |
| Container registry | Amazon ECR |
| CI/CD | GitHub Actions |
| Secret management | AWS Secrets Manager + GitHub Actions OIDC |
| Observability | CloudWatch Logs + X-Ray |

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Node.js | 20 LTS | Use [nvm](https://github.com/nvm-sh/nvm) or [fnm](https://github.com/Schniz/fnm) |
| npm | 10 | Bundled with Node 20 |
| Docker & Docker Compose | 24 / 2.20 | Required for local database |
| PostgreSQL client | 15 | Optional — only for direct DB access |
| AWS CLI | 2 | Optional — only for infra tasks |

---

## Getting Started

### Environment Variables

Copy the example files and fill in your local values:

```bash
cp frontend/.env.example frontend/.env.local
cp backend/.env.example  backend/.env
```

Key variables:

| Variable | App | Description |
|----------|-----|-------------|
| `NEXT_PUBLIC_API_URL` | frontend | Base URL of the backend API visible in the browser |
| `API_INTERNAL_URL` | frontend | Base URL used server-side (RSC / route handlers) |
| `DATABASE_URL` | backend | PostgreSQL connection string |
| `SESSION_SECRET` | backend | ≥32-character secret for session signing |
| `COOKIE_DOMAIN` | backend | Domain for session cookies |
| `PORT` | backend | HTTP port (default `4000`) |

> **Security note:** Never commit `.env` or `.env.local` files. All production secrets are stored in AWS Secrets Manager and injected at runtime.

---

### Install Dependencies

Install each workspace independently (no root-level hoisting):

```bash
# Frontend
cd frontend && npm ci

# Backend
cd backend  && npm ci
```

---

### Run in Development

**Option A — two terminals:**

```bash
# Terminal 1 — start the database
docker compose up postgres

# Terminal 2 — backend (http://localhost:4000)
cd backend
npx prisma migrate dev
npm run dev

# Terminal 3 — frontend (http://localhost:3000)
cd frontend
npm run dev
```

**Option B — all services via Docker Compose:**

```bash
docker compose up --build
```

The frontend is available at **http://localhost:3000** and the API at **http://localhost:4000**.

---

### Run with Docker Compose

The `docker-compose.yml` at the repo root defines three services:

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL 15 database |
| `backend` | 4000 | Express API (hot-reload via `ts-node-dev`) |
| `frontend` | 3000 | Next.js dev server |

```bash
docker compose up           # start all services
docker compose up postgres  # start only the DB
docker compose down -v      # stop and remove volumes
```

---

## Available Scripts

### Frontend (`frontend/`)

| Script | Description |
|--------|-------------|
| `npm run dev` | Start Next.js dev server with HMR |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | ESLint |
| `npm run type-check` | `tsc --noEmit` |
| `npm test` | Jest unit / component tests |
| `npm run test:e2e` | Playwright end-to-end tests |

### Backend (`backend/`)

| Script | Description |
|--------|-------------|
| `npm run dev` | Start with hot-reload (`ts-node-dev`) |
| `npm run build` | Compile TypeScript to `dist/` |
| `npm run start` | Run compiled output |
| `npm run lint` | ESLint |
| `npm run type-check` | `tsc --noEmit` |
| `npm test` | Vitest unit + integration tests |
| `npm run db:migrate` | `prisma migrate dev` |
| `npm run db:studio` | Open Prisma Studio |

---

## Testing

```
# Unit + component tests (frontend)
cd frontend && npm test

# Unit + integration tests (backend)
cd backend && npm test

# End-to-end tests (requires both servers running)
cd frontend && npm run test:e2e
```

CI runs all three suites on every pull request. See `.github/workflows/` for full pipeline details.

---

## Code Quality

- **ESLint** enforces project-specific rules (Next.js core, React hooks, accessibility via `jsx-a11y`, import ordering).
- **Prettier** handles formatting; configured at the workspace level.
- **TypeScript strict mode** is enabled in both workspaces — no `any`, no unsafe assertions.
- **Pre-commit hooks** (via [Husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/lint-staged/lint-staged)) run lint and type-check on staged files.

Run all checks manually:

```bash
cd frontend && npm run lint && npm run type-check
cd backend  && npm run lint && npm run type-check
```

---

## Deployment

Deployments are fully automated via GitHub Actions:

| Branch / Event | Action |
|----------------|--------|
| PR opened / updated | Lint, type-check, unit tests, build check |
| Merge to `main` | Build & push Docker images to ECR → deploy to **staging** (ECS Fargate) |
| Release tag `v*` | Promote staging image to **production** |

Infrastructure changes require a separate `infra/` workflow approval gate. See [`docs/architecture.md`](docs/architecture.md) for the full deployment topology.

---

## Contributing

Please read [`docs/contributing.md`](docs/contributing.md) before opening a pull request. Key points:

- Create a feature branch from `main`: `git checkout -b feat/your-feature`.
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).
- All PRs require at least one approving review and a passing CI pipeline.
- Security findings must be reported privately — see `SECURITY.md` for the responsible disclosure policy.

---

## License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for details.
