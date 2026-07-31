---

## Phase 1/3

ROUTE TO SKILL: TASK-010 — Infrastructure-as-Code (AWS Aurora / ElastiCache provisioning)

---

## Why This Phase Is Blocked Here

TASK-010 ("Provision Aurora/RDS cluster with KMS encryption") and the PHASE-006 exit criteria ("Aurora cluster Multi-AZ posture + Redis replication group reachable from private subnets only") are **exclusively infrastructure provisioning work**, not FastAPI/Python application code:

| Item | Nature | Correct skill |
|---|---|---|
| Aurora cluster, Multi-AZ, KMS CMK | AWS IaC resource | IaC skill (Terraform / CDK / CloudFormation) |
| ElastiCache Redis replication group | AWS IaC resource | IaC skill |
| Private-subnet-only network exposure | VPC / security-group config | IaC skill |
| KMS key + key policy | AWS KMS IaC | IaC skill |

Per **§3 of the Implementation Contract**: infrastructure-as-code tasks must be routed to the IaC skill; this skill must not emit a substitute Python implementation for them, and doing so would produce an incorrect, non-deployable artifact.

---

## What the FastAPI Backend Skill **will** contribute (in a later phase)

Once the IaC skill has provisioned the Aurora cluster and Redis replication group and exported the relevant connection strings / ARNs, this skill will:

- Wire `DATABASE_URL` (async Aurora writer endpoint) and `REDIS_URL` into `backend/app/core/config.py` via `pydantic-settings`
- Configure the SQLAlchemy 2.0 async engine + session factory against the Aurora endpoint
- Configure the Redis client (e.g., `redis.asyncio`) against the ElastiCache endpoint
- Add a `/healthz` readiness probe that asserts both stores are reachable

That work is **dependent** on PHASE-006 IaC outputs and should be scheduled after the IaC phase closes.

---

## Completed / Blocked / Deferred

- **Blocked:** TASK-010 — requires IaC skill; no FastAPI/Python deliverable exists for this task
- **Deferred:** Backend data-store wiring — depends on TASK-010 IaC outputs (connection endpoints, KMS ARN, secret ARN)

---

## Phase 2/3

ROUTE TO SKILL: TASK-010 — IaC skill (Terraform/CDK/CloudFormation) · `infra/data/aurora.tf`
ROUTE TO SKILL: TASK-011 — IaC skill (Terraform/CDK/CloudFormation) · `infra/data/elasticache.tf`

---

## Why This Phase Is Blocked Here (Again)

Both tasks in Phase 2/3 are **exclusively AWS infrastructure provisioning work**. The target files (`infra/data/aurora.tf`, `infra/data/elasticache.tf`) are Terraform HCL, not Python. Per **§3 of the Implementation Contract**, this skill must not emit a substitute implementation and must not produce `.tf` files:

| Task | File | Nature | Correct skill |
|---|---|---|---|
| TASK-010 | `infra/data/aurora.tf` | Aurora cluster, Multi-AZ, KMS CMK, subnet group, security group | **IaC skill** |
| TASK-011 | `infra/data/elasticache.tf` | ElastiCache Redis replication group, subnet group, security group, at-rest encryption | **IaC skill** |

Emitting Terraform from the FastAPI/Python skill would produce a non-deployable artifact, bypass IaC review gates, and violate the aws_only guardrail's requirement that IaC target only approved AWS resources via an enterprise-approved tool (§ aws_only rule 6).

---

## Completed / Blocked / Deferred

- **Blocked:** TASK-010 — IaC skill required; no FastAPI/Python deliverable
- **Blocked:** TASK-011 — IaC skill required; depends on TASK-010 VPC/subnet outputs; no FastAPI/Python deliverable
- **Deferred:** Backend data-store wiring (`DATABASE_URL`, `REDIS_URL`, SQLAlchemy async engine, Redis client, `/healthz` probe) — depends on TASK-010 and TASK-011 IaC outputs (writer endpoint, Redis primary endpoint, KMS ARN, Secrets Manager ARN)

---

## Phase 3/3

Applying **§3 of the Implementation Contract** and the same analysis already performed in Phase 1.

---

## Phase 3 Routing Decision

### ROUTE TO SKILL: Phase 3 acceptance criteria — IaC skill (Terraform / CDK / CloudFormation)

| Acceptance Criterion | Nature | Correct Skill |
|---|---|---|
| "Redis reachable only from app subnet" | ElastiCache subnet group + VPC security-group rule scoped to app-tier CIDR | **IaC skill** |
| "Multi-AZ replication enabled" | `ElastiCache::ReplicationGroup` with `AutomaticFailoverEnabled: true`, `MultiAZEnabled: true`, ≥2 replica nodes across AZs | **IaC skill** |
| Connectivity + failover smoke test (infrastructure leg) | `redis-cli` / AWS CLI failover API call verifying primary promotion | **IaC / Ops skill** |

Every item in the Phase 3 acceptance criteria is an **AWS infrastructure provisioning and network-topology concern**, not FastAPI/Python application code. Emitting Python stubs that fabricate these controls would produce non-deployable, non-verifiable artifacts and would contradict the routing decision already recorded in Phase 1.

---

### What the FastAPI backend skill will deliver — once IaC outputs exist

As noted in the Phase 1 block report, **these backend deliverables remain deferred** pending IaC outputs (Redis primary endpoint, auth token / Secrets Manager ARN, VPC-internal DNS):

| Deliverable | Depends on |
|---|---|
| `REDIS_URL` wired into `backend/app/core/config.py` via `pydantic-settings` | ElastiCache primary endpoint (IaC output) |
| `redis.asyncio` client in FastAPI lifespan | `REDIS_URL` config value |
| `/healthz` readiness probe asserting Redis `PING` | Redis client + endpoint |
| Async connectivity + failover integration test (`pytest`, HTTPX `ASGITransport`) | Live Redis endpoint reachable from CI subnet |

These will be implemented in full, with no placeholders, as soon as the IaC phase closes and exports its connection outputs.

---

## Completed / Blocked / Deferred

- **Blocked — Phase 3 IaC tasks:** Require IaC skill; no FastAPI/Python deliverable exists. Routing: **IaC skill → ElastiCache `ReplicationGroup` resource + VPC security-group + subnet group configuration.**
- **Deferred — Backend Redis wiring + `/healthz` + connectivity test:** Depends on Phase 3 IaC outputs (`REDIS_URL`, Secrets Manager ARN). Ready to implement immediately once those outputs are available.