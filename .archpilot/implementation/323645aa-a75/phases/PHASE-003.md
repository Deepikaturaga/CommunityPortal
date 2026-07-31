---

## Phase 1/3

ROUTE TO SKILL: TASK-005 — AWS Infrastructure-as-Code (IaC)

---

## Routing Decision

TASK-005 and the broader PHASE-003 objective contain **no FastAPI/Python backend work**. Every exit criterion maps exclusively to AWS infrastructure provisioning:

| Task / Exit Criterion | Required Capability | Routed Skill |
|---|---|---|
| TASK-005: CloudWatch log groups | AWS resource creation (IaC) | IaC / CDK / Terraform |
| TASK-005: X-Ray tracing *activation* | AWS resource creation (IaC) | IaC / CDK / Terraform |
| Phase exit: WAF attached to edge | AWS WAF + CloudFront/ALB wiring (IaC) | IaC / CDK / Terraform |
| Phase exit: Managed rule groups | AWS WAF RuleGroup resources (IaC) | IaC / CDK / Terraform |

Per Implementation Contract §3:

> *For infrastructure-as-code, emit `ROUTE TO SKILL` and no substitute implementation. Never translate an infra task into Python.*

---

## Boundary Clarification

There **is** a narrow Python/FastAPI component that will be needed downstream (e.g., adding `aws-xray-sdk` or OpenTelemetry → ADOT instrumentation to the FastAPI app, structured JSON logging to stdout for CloudWatch ingestion). That work belongs here **only when** a task explicitly scopes application-layer instrumentation and the PHASE-001 backend foundation exists to patch. It should be filed as a distinct backend task (e.g., "Instrument FastAPI app with X-Ray SDK + structured logging") rather than bundled with log group and WAF provisioning.

---

## Completed / Blocked / Deferred

- **Completed:** —
- **Blocked:** TASK-005 — wrong skill; no FastAPI/Python deliverable present in scope.
- **Deferred:** Application-layer X-Ray SDK instrumentation (if required) — needs explicit backend task scoped against the canonical `backend/` app, depends on PHASE-001 output.

Please direct TASK-005 to the **IaC skill** (Terraform/CDK). Once that phase lands the infrastructure and a backend instrumentation task is created, this skill can patch `backend/app/main.py`, `backend/app/core/config.py`, and `backend/pyproject.toml` with the SDK wiring.

---

## Phase 2/3

ROUTE TO SKILL: TASK-005 (structured logging / observability wiring) and TASK-006 (WAF attachment) — **AWS Infrastructure-as-Code (Terraform/CDK)**

---

## Routing Decision

Neither task in this phase contains FastAPI/Python backend work. Every deliverable and acceptance criterion maps exclusively to AWS infrastructure provisioning via Terraform:

| Task | File Area | Required Capability | Routed Skill |
|---|---|---|---|
| TASK (observability) | `infra/observability/*.tf` | CloudWatch log groups, X-Ray groups, metric filters | IaC / Terraform |
| TASK-006 | `infra/waf/*.tf` | `aws_wafv2_web_acl`, managed rule groups, ALB/CloudFront association | IaC / Terraform |

Per Implementation Contract §3:

> *For infrastructure-as-code, emit `ROUTE TO SKILL` and no substitute implementation. Never translate an infra task into Python.*

---

## Boundary Clarification — Backend Component (Deferred)

NFR-016 ("Structured JSON logs with correlation ID") **does** have an application-layer component that belongs to this skill — but only the application-side half:

| Layer | Owner | Status |
|---|---|---|
| CloudWatch log group + metric filters | IaC skill (`infra/observability/*.tf`) | Route to IaC |
| FastAPI structured JSON logging middleware + correlation-ID propagation to stdout | **This skill** (`backend/app/middleware/logging.py`, patch `backend/app/main.py`) | **Deferred — needs explicit backend task** |
| X-Ray SDK / ADOT instrumentation in the FastAPI app | **This skill** (`backend/app/core/tracing.py`) | **Deferred — needs explicit backend task** |

The application-layer work is ready to implement as soon as:
1. The IaC phase lands (log group ARN and X-Ray group name available as outputs).
2. A backend task is explicitly created scoped to `backend/` (e.g., *"Instrument FastAPI with structured JSON logging + correlation ID middleware"*).

---

## Completed / Blocked / Deferred

- **Completed:** —
- **Blocked:** Both Phase 2 tasks — wrong skill; file areas are `infra/**/*.tf` (Terraform), not `backend/`.
- **Deferred:**
  - Application-layer structured logging middleware (`backend/app/middleware/logging.py`) — needs explicit backend task + IaC outputs.
  - X-Ray SDK instrumentation (`backend/app/core/tracing.py`) — same dependency.

Please direct both tasks to the **IaC skill** (Terraform). Once that phase is complete and a backend instrumentation task is filed against `backend/`, this skill will patch the canonical FastAPI app with the correlation-ID middleware and tracing setup.

---

## Phase 3/3

---

# Phase 3/3 — Routing Decision

## Analysis

The sole task in this phase has the following acceptance criteria:

| Acceptance Criterion | Required Capability | Deliverable Type |
|---|---|---|
| WAF blocks common attack signatures (OWASP managed rules) | AWS WAF `ManagedRuleGroup` resource, associated to CloudFront/ALB | AWS IaC (Terraform/CDK) |
| WAF test-mode log shows rule matches on malicious sample requests | AWS WAF logging configuration + CloudWatch log group + override action `COUNT` | AWS IaC (Terraform/CDK) |

**There is no FastAPI/Python deliverable in this task.**

Per Implementation Contract §3:

> *For frontend, infrastructure-as-code, documentation, penetration-testing, or deployment-only tasks, emit `ROUTE TO SKILL` and no substitute implementation. Never translate an infra task into Python.*

---

## ROUTE TO SKILL: Phase 3 WAF task — AWS IaC (Terraform/CDK)

The complete surface area of this task lives in AWS:

1. **`aws_wafv2_web_acl`** (or CDK `CfnWebACL`) — add `AWSManagedRulesCommonRuleSet`, `AWSManagedRulesKnownBadInputsRuleSet`, and any other OWASP-mapped managed rule groups.
2. **Override actions** — set rule groups to `COUNT` (test/log-only mode) initially so WAF test-mode log can show matches without blocking legitimate traffic during validation.
3. **`aws_wafv2_web_acl_logging_configuration`** — point WAF logs to the CloudWatch log group provisioned by TASK-005.
4. **ACL association** — attach the WebACL to the CloudFront distribution or ALB ARN provisioned in earlier infrastructure phases.
5. **Validation** — use `aws wafv2 check-capacity` and `aws wafv2 get-sampled-requests` (or WAF test traffic via `curl`/`awscurl` with known-bad payloads) to confirm `COUNT` rule matches appear in CloudWatch Logs Insights; then flip override to `BLOCK` once validated.

None of these resources are expressible as Python/FastAPI code. Writing stub Python to "simulate" WAF behavior would be fabricated functionality (prohibited by §7 of the contract).

---

## Boundary Note for the Backend Skill

Once the IaC phase lands the WAF, there **is** a narrow backend-owned follow-up that belongs here:

| Future Backend Task | File(s) Affected | Dependency |
|---|---|---|
| Add `X-Forwarded-For` / `X-Amzn-Trace-Id` header propagation to structured request logs so WAF block events correlate to application traces | `backend/app/middleware/logging.py` | TASK-005 CloudWatch + WAF logging |
| Return `429` from the FastAPI rate-limit middleware when WAF sends a `x-amzn-waf-action: block` header downstream (if using ALB passthrough mode) | `backend/app/middleware/security.py` | WAF ACL association |

File that as an explicit backend instrumentation task against the canonical `backend/` app after the IaC skill delivers the WAF ACL ARN.

---

## Completed / Blocked / Deferred

- **Completed:** —
- **Blocked:** Phase 3 WAF task — wrong skill; zero FastAPI/Python deliverables present in scope.
- **Deferred:** Application-layer WAF correlation logging + header propagation — needs an explicit backend task after IaC delivers the WAF ACL and CloudWatch log group ARNs.

**Direct this phase to the IaC skill (Terraform/CDK).** No files were written; the repository is unchanged.