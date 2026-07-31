---

## Phase 1/3

---

## Routing & Blocking Analysis

### ROUTE TO SKILL + BLOCKED

**TASK-003 — Configure CI pipeline (build/test/SAST/SCA)**

`ROUTE TO SKILL: TASK-003 — DevOps / CI-CD / IaC skill required`

Two independent reasons this task cannot be executed by the Python FastAPI Implementation Skill:

---

#### Reason 1 — Wrong skill boundary (§3, §2a)

The implementation contract is explicit:

> *For frontend, **infrastructure-as-code**, documentation, penetration-testing, or **deployment-only** tasks, emit `ROUTE TO SKILL` and no substitute implementation.*

And in §2a (canonical monorepo layout):

> *Only shared, repo-wide files belong at the root: `.gitignore`, top-level `README.md`, **CI under `.github/workflows/`**, IaC under `infra/`. **Those are owned by other skills.***

TASK-003 is entirely composed of:

| Deliverable | Category | This skill? |
|---|---|---|
| GitHub Actions (or equivalent) workflow YAML | CI/CD / DevOps | ❌ other skill |
| SAST tool config (Semgrep / Bandit / CodeQL) | Security scanning tooling | ❌ other skill |
| SCA tool config (Snyk / pip-audit / Safety) | Dependency scanning | ❌ other skill |
| Branch-protection / merge-gate rules | CI/CD / repo governance | ❌ other skill |
| IaC plan-review workflow (Terraform/Terragrunt) | IaC / DevOps | ❌ other skill |

Writing these files here would silently violate the routing contract and produce orphaned artefacts no other phase expects.

---

#### Reason 2 — Authoritative context missing (§1, §2)

Even if routing were acceptable, the task cannot be safely implemented without:

| Missing context | Why it blocks |
|---|---|
| CI platform (GitHub Actions, GitLab CI, CircleCI, Buildkite…) | Workflow syntax is platform-specific |
| SAST/SCA tool selection and version policy | Tool configs, severity mappings, suppression policy differ per tool |
| "Critical/high" severity definition | Thresholds differ between Semgrep, CodeQL, Snyk, pip-audit |
| IaC tool (Terraform / Tofu / CDK) and state-backend location | Plan-review step is tool-specific |
| AWS account/region scope for IaC apply gate | Required by `aws_only` guardrail |
| Approved branch model / PR merge strategy | Gate wiring depends on branch topology |
| PHASE-001 outputs (repo structure, lockfile format, test command) | Build/test step depends on what PHASE-001 produced |

`BLOCKED: authoritative context missing — CI platform, SAST/SCA tool selection, IaC toolchain, severity thresholds, AWS target account/region, and PHASE-001 outputs are all absent (§1, §2, aws_only guardrail)`

---

## What needs to happen before this task can proceed

1. **PHASE-001 must close first** (the task's own stated dependency) so the build/test commands and lockfile format are known.
2. The following decisions must be recorded in the authoritative context and handed to the **DevOps / CI-CD skill**:

   - CI platform selection
   - SAST tool + version (e.g. Semgrep OSS `1.x`, CodeQL, Bandit)
   - SCA tool + version (e.g. `pip-audit`, Snyk, Safety)
   - Severity threshold policy (what constitutes "critical/high" per tool)
   - IaC tool and remote state backend (S3 + DynamoDB lock table, per `aws_only`)
   - AWS accounts for staging/prod and who owns the apply-gate approval
   - Branch model (trunk, gitflow, etc.) and required reviewers

3. Once those decisions exist, route the task to the **DevOps / CI-CD / IaC skill** which owns `.github/workflows/` and `infra/`.

---

## Completed / Blocked / Deferred

| Status | Task |
|---|---|
| **Blocked** | TASK-003 — wrong skill boundary + missing authoritative context |
| Deferred | All downstream tasks that depend on TASK-003 |

---

## Phase 2/3

ROUTE TO SKILL: Phase 2 tasks — DevOps / CI-CD / IaC skill required

Both tasks in this phase fall entirely outside the Python FastAPI Implementation Skill boundary. No files will be written.

---

## Routing Decision

### Unnamed pipeline task (vulnerability gate, CON-004 / NFR-010 / VER-015)

| Deliverable | Category | This skill? |
|---|---|---|
| `.github/workflows/*.yml` (or CodePipeline config) | CI/CD / DevOps | ❌ other skill |
| Vulnerability-severity gate logic | Security scanning tooling / CI | ❌ other skill |
| Intentional-failure test harness for VER-015 | CI pipeline testing | ❌ other skill |

Governed by **§3** (*"infrastructure-as-code, deployment-only tasks → emit `ROUTE TO SKILL`"*) and **§2a** (*"CI under `.github/workflows/` … owned by other skills"*).

---

### TASK-004 — IaC plan-review gate (`infra/ci/*`)

| Deliverable | Category | This skill? |
|---|---|---|
| `infra/ci/*` plan-review gate | IaC / DevOps | ❌ other skill |
| Staging/prod apply approval workflow | CI/CD / repo governance | ❌ other skill |

Same governing clauses: **§3** and **§2a** — IaC lives under `infra/`, owned by the IaC/DevOps skill.

---

## Completed / Blocked / Deferred

- **Completed:** _(none — no in-scope backend tasks present in this phase)_
- **Blocked:** _(none — no ambiguity requiring a decision)_
- **Deferred / Routed:**
  - Pipeline vulnerability-gate task → `ROUTE TO SKILL: DevOps / CI-CD skill`
  - `TASK-004` → `ROUTE TO SKILL: IaC / DevOps skill`

---

## Notes

Both tasks mirror the same routing decision already established for **TASK-003 in Phase 1**. If Phase 3 contains Python/FastAPI backend tasks (models, routes, services, migrations, tests), those will be implemented under `backend/` per the canonical monorepo layout. Please confirm Phase 3 task list when ready.

---

## Phase 3/3

## Pre-flight Analysis — Phase 3/3

Before writing any files I must apply §1 (authoritative context), §3 (skill boundary), and §2 (structural pre-flight) checks.

---

### BLOCKED + ROUTE TO SKILL: Phase 3 Task — IaC Plan-Review Gate

#### Dependency block (§1)

The sole task in this phase carries an explicit dependency:

> **Depends On: TASK-003**

TASK-003 was routed out of this skill in Phase 1 with the finding:

> `ROUTE TO SKILL: TASK-003 — DevOps / CI-CD / IaC skill required`

A downstream task that depends *entirely* on a routed-out parent cannot be unblocked here. There is no Python/FastAPI artifact this skill can produce that satisfies the gate TASK-003 was supposed to establish.

---

#### Wrong skill boundary (§3)

The acceptance criterion and validation statement are unambiguously IaC/CI-CD in nature:

| Deliverable implied | Category | This skill? |
|---|---|---|
| "reviewed plan artifact" — Terraform/Tofu plan output | IaC plan workflow | ❌ DevOps/IaC skill |
| "unreviewed apply is rejected" — merge/apply gate | CI/CD branch-protection gate | ❌ DevOps/IaC skill |
| Manual test of the gate enforcement | CI/CD runtime validation | ❌ DevOps/IaC skill |

Per §2a and §3, CI workflow files and IaC plan-review gates live under `.github/workflows/` or `infra/` — owned by the DevOps/IaC skill, never the FastAPI Implementation Skill.

---

#### Authoritative context missing (§1)

Even if routing were acceptable, the following required context is absent:

| Missing item | Why it blocks |
|---|---|
| IaC tool (Terraform / OpenTofu / CDK / Pulumi) | Plan artifact format, CLI commands, and gate mechanism differ entirely per tool |
| CI platform | Workflow syntax is platform-specific |
| "Reviewed plan artifact" definition | Could be Atlantis PR comment, a GitHub Actions artifact, a Conftest policy output, etc. |
| State backend and AWS account/region | Required to run `plan` at all (AWS-only guardrail §aws_only) |
| Who performs the review and how approval is recorded | Determines whether the gate is a required reviewer, an environment protection rule, or a policy check |

---

## Completed / Blocked / Deferred

| Status | Task | Reason |
|---|---|---|
| **Blocked** | Phase 3 unnamed task (depends on TASK-003) | Parent TASK-003 routed to DevOps/IaC skill; task content is outside FastAPI skill boundary; authoritative IaC/CI context missing |

**Completed:** *(none — no in-scope FastAPI work exists in this phase)*

**Deferred:** *(none — this task cannot be deferred to a later FastAPI phase; it must be handled by the DevOps/IaC skill)*

---

## Notes

No files were written. Writing a placeholder, stub workflow YAML, or fake `plan`-check script would violate §3 (routing contract), §1 (no invented behavior), and §7 (no placeholder implementations). The correct action is to forward this task to the DevOps/IaC skill with the missing context items listed above resolved first.