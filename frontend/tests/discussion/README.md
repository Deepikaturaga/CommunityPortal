# Discussion & Moderation Test Suite — PHASE-024

## VER-002 · VER-020 Exit Criteria

This directory contains the complete frontend test suite for discussion and moderation features.
All tests run via **Jest 29 + MSW v2** (Node server mode) against a typed API client that
mirrors the backend OpenAPI contract.

## Running Tests

```bash
cd frontend

# Install (first time)
npm install

# Run the full discussion suite with coverage
npm run test:ci

# Run in watch mode during development
npm test -- --watch --testPathPattern=tests/discussion

# Run a single file
npm test -- tests/discussion/rateLimit.test.ts
```

## Acceptance Criteria Coverage

| AC Group | File | Tests |
|---|---|---|
| AC-009.x — Thread creation | `threadCreation.test.ts` | 10 |
| AC-010.x — Reply creation | `replyCreation.test.ts` | 10 |
| AC-011.x — Thread listing/pagination | `threadListing.test.ts` | 9 |
| AC-012.x — Thread detail + reply tree | `threadDetail.test.ts` | 8 |
| AC-013.x — Moderation actions | `moderation.test.ts` | 9 |
| AC-014.x — Role-gating | `moderationRoleGating.test.ts` | 8 |
| AC-015.x — Rate limiting | `rateLimit.test.ts` | 8 |
| **Total** | | **62** |

## Architecture

```
tests/discussion/
├── mocks/
│   ├── handlers.ts       # MSW v2 request handlers (stateful rate-limit counter)
│   └── server.ts         # setupServer() export
├── threadCreation.test.ts
├── replyCreation.test.ts
├── threadListing.test.ts
├── threadDetail.test.ts
├── moderation.test.ts
├── moderationRoleGating.test.ts
└── rateLimit.test.ts

src/lib/api/
├── types.ts              # Canonical API contract types (single source of truth)
└── discussionApi.ts      # Fetch-based API client (cookie auth, typed errors)
```

## Security Notes (OWASP)

- **A01 Broken Access Control**: Role-gating tests (AC-014.x) assert 401/403 for unauthenticated
  and member roles; AC-014.6 verifies the 403 message exposes no internal role/permission details.
- **A02 Cryptographic Failures**: Auth transport uses HTTP-only cookies (`credentials: "include"`);
  no tokens stored in `localStorage` or exposed in client bundles.
- **A05 Security Misconfiguration**: Rate-limit 429 responses are generic (`"Too Many Requests"` only);
  tests in AC-015.3 verify no retry-after timing, quota, or user information leaks.
