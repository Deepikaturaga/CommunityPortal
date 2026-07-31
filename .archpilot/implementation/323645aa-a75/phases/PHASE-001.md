---

## Phase 1/3

ROUTE TO SKILL: TASK-001 — Infrastructure-as-Code (AWS VPC / networking / compute provisioning)

---

## Why this phase is out of scope for the FastAPI Implementation Skill

PHASE-001 / TASK-001 contains **exclusively AWS infrastructure provisioning work**:

| Task | Required capability | This skill? |
|---|---|---|
| TASK-001: Provision VPC/subnets/route tables | IaC (Terraform / CDK / CloudFormation) targeting AWS networking primitives | ❌ — IaC Skill |
| Exit criterion: ECS/Fargate compute target reachable via test deploy | AWS ECS/Fargate provisioning + deployment | ❌ — IaC Skill |

Per **Implementation Contract §3**:

> *For frontend, infrastructure-as-code, documentation, penetration-testing, or deployment-only tasks, emit `ROUTE TO SKILL: <task ID> — <required capability>` and no substitute implementation. Never translate an infra task into Python or a frontend task into route stubs.*

Writing stub Python files or placeholder Terraform to appear busy would be a contract violation and would produce un-runnable artifacts that conflict with whatever the IaC skill generates.

---

## What to do next

1. **Route PHASE-001 to the IaC skill** (Terraform / AWS CDK / CloudFormation — whichever your enterprise standard mandates per the `aws_only` guardrail).
2. The IaC skill should produce at minimum:
   - VPC + public/private subnets across ≥ 2 AZs
   - Route tables + Internet Gateway / NAT Gateway
   - Security groups (ALB ingress, ECS task, RDS)
   - IAM roles (ECS task execution role, task role)
   - ECS cluster + Fargate capacity provider
3. **Once PHASE-001 exits**, return here for **PHASE-002 / PHASE-003** — the FastAPI Implementation Skill will wire the application to the VPC, subnets, security-group IDs, and IAM role ARNs that the IaC skill outputs (typically via SSM Parameter Store references or Terraform remote state).

---

## Completed / Blocked / Deferred

- **Completed:** *(none — no Python backend work in this phase)*
- **Blocked:** TASK-001 — not a Python/FastAPI task; requires IaC skill
- **Deferred:** PHASE-002, PHASE-003 — pending PHASE-001 exit criteria being met by IaC skill

---

## Phase 2/3

ROUTE TO SKILL: TASK-002 — Infrastructure-as-Code (AWS IAM roles/policies via Terraform/CDK)
ROUTE TO SKILL: VPC/subnet task — Infrastructure-as-Code (AWS VPC networking via Terraform/CDK)

---

## Why Phase 2 is also out of scope for the FastAPI Implementation Skill

Every task listed in this phase is **exclusively AWS IaC work**:

| Task | Files | Required capability | This skill? |
|---|---|---|---|
| VPC / subnets / route tables | `infra/network/*.tf` | Terraform AWS networking primitives | ❌ — IaC Skill |
| TASK-002: IAM roles/policies | `infra/iam/*.tf` | Terraform AWS IAM resources | ❌ — IaC Skill |

Per **Implementation Contract §3**, writing Terraform (or CDK) for AWS VPCs and IAM roles is not Python/FastAPI backend work. Producing stub `.tf` files here would:

1. **Conflict** with whatever the IaC Skill generates (duplicate resource definitions cause `terraform apply` failures).
2. **Violate the `aws_only` guardrail** by producing unvalidated IaC outside the approved toolchain and review process.
3. **Produce un-runnable artifacts** — Terraform requires provider configuration, state backends, and variable files that only the IaC Skill owns.

---

## What the IaC Skill should deliver for these tasks

**VPC task (`infra/network/*.tf`):**
- VPC + public/private subnets across ≥ 2 AZs
- Internet Gateway, NAT Gateway(s)
- Route tables (public: IGW; private: NAT)
- VPC Flow Logs → CloudWatch (audit requirement)

**TASK-002 (`infra/iam/*.tf`):**
- ECS Task Execution Role (pull from ECR, write to CloudWatch Logs)
- ECS Task Role (least-privilege: only the AWS APIs the application actually calls — no `*` actions, no long-lived access keys)
- Secrets Manager read policy scoped to the app's secret ARN prefix
- RDS IAM auth policy if the app uses IAM-auth database connections
- Boundary/permission policy to prevent privilege escalation

**Validation evidence (VER-018):** `terraform validate` + `terraform plan` output showing zero errors, zero unintended resource changes, and IAM policy documents reviewed by `aws iam simulate-principal-policy` or equivalent.

---

## What happens next

| Phase | Skill | Gate |
|---|---|---|
| Phase 2 (current) | **IaC Skill** | `terraform apply` clean; outputs (VPC ID, subnet IDs, SG IDs, task role ARN, execution role ARN) written to SSM Parameter Store or Terraform remote state |
| Phase 3 | **FastAPI Implementation Skill** | Reads IaC outputs; wires `DATABASE_URL`, `AWS_REGION`, secret ARN refs into `pydantic-settings`; implements application endpoints, migrations, auth, and tests |

Return here once Phase 2 IaC outputs are available — the FastAPI skill will reference them as environment/SSM inputs rather than hardcoded values.

---

## Completed / Blocked / Deferred

- **Completed:** *(none — no Python backend work in this phase)*
- **Blocked:** VPC task, TASK-002 — routed to IaC Skill; no FastAPI/Python deliverable exists for these tasks
- **Deferred:** Phase 3 FastAPI application implementation — pending IaC output availability

---

## Phase 3/3

ROUTE TO SKILL: TASK (Phase 3 IAM roles) — Infrastructure-as-Code / AWS IAM (ECS task roles, Lambda execution roles, IAM policy linting)

---

## Why this phase contains no FastAPI backend work

Every acceptance criterion in this phase is an **AWS IAM / IaC deliverable**, not a Python/FastAPI one:

| Acceptance Criterion | Required Capability | This Skill? |
|---|---|---|
| ECS task roles scoped per module | AWS IAM Role + Trust Policy (IaC) | ❌ — IaC Skill |
| Lambda execution roles scoped per module | AWS IAM Role + Trust Policy (IaC) | ❌ — IaC Skill |
| No static access keys | IAM design constraint enforced in IaC / policy | ❌ — IaC Skill |
| Validation: `cfn-policy-validator` / manual review | CloudFormation / IAM policy lint tooling | ❌ — IaC Skill |

Per **Implementation Contract §3**:

> *For frontend, infrastructure-as-code, documentation, penetration-testing, or deployment-only tasks, emit `ROUTE TO SKILL: <task ID> — <required capability>` and no substitute implementation. Never translate an infra task into Python or a frontend task into route stubs.*

Writing stub Python or placeholder IAM JSON to appear busy would be a contract violation and would conflict with whatever the IaC skill generates.

---

## What to do next

Route this phase to the **IaC Skill** (Terraform / AWS CDK / CloudFormation per your enterprise standard and the `aws_only` guardrail). That skill should produce at minimum:

1. **ECS task execution role** — `ecs-tasks.amazonaws.com` trust, scoped to ECR pull + CloudWatch Logs only.
2. **ECS task role(s)** — one per module/service, least-privilege policies referencing only the SSM/Secrets Manager paths, S3 buckets, SQS queues, etc. that module actually consumes. No `*` resource policies.
3. **Lambda execution role(s)** — `lambda.amazonaws.com` trust, one per function/module, scoped to the exact managed policy (`AWSLambdaBasicExecutionRole` or VPC variant) plus any additional resource-level grants.
4. **Explicit denial of `iam:CreateAccessKey` / `iam:CreateUser`** in a Service Control Policy (SCP) or permission boundary to enforce the "no static access keys" criterion at the account level.
5. **IAM policy lint** via `cfn-policy-validator` (or `aws-iam-policy-validator` / `checkov` as applicable) wired into CI — the IaC skill owns this validation step.

---

## Completed / Blocked / Deferred

- **Completed:** *(none — no Python backend work in this phase)*
- **Blocked:** All Phase 3 tasks — wrong skill; must be routed to the IaC Skill.
- **Deferred:** *(none)*