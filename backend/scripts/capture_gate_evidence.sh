#!/usr/bin/env bash
# =============================================================================
# capture_gate_evidence.sh — TASK-012 / PHASE-007
# =============================================================================
# PURPOSE
#   Run both security gates locally (or in CI outside GitHub Actions), capture
#   structured evidence JSON for VER-015 and VER-018, and exit non-zero if
#   either gate's DRY-RUN fails to block.
#
# USAGE
#   cd backend/
#   bash scripts/capture_gate_evidence.sh
#
# OUTPUTS
#   tests/evidence/ver-015-evidence.json  — SCA gate evidence (VER-015)
#   tests/evidence/ver-018-evidence.json  — Secret-scan gate evidence (VER-018)
#   tests/evidence/capture-summary.json  — Combined run summary
#
# EXIT CODES
#   0 — both gates blocked correctly (fixtures triggered scanners as expected)
#   1 — one or both gates FAILED to block (gate is broken)
#   2 — tool not installed / setup error
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
EVIDENCE_DIR="${BACKEND_DIR}/tests/evidence"
FIXTURES_DIR="${BACKEND_DIR}/tests/fixtures"

VULN_REQ="${FIXTURES_DIR}/requirements-vulnerable.txt"
SECRETS_FX="${FIXTURES_DIR}/secrets_fixture.py"

TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
OVERALL_PASS=0   # 0 = all good; incremented on failure

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
log()  { echo "[$(date -u +"%H:%M:%S")] $*"; }
fail() { echo "[FAIL] $*" >&2; }
pass() { echo "[PASS] $*"; }

require_tool() {
    if ! python -m "${1}" --version &>/dev/null 2>&1; then
        echo "ERROR: Python module '${1}' not found. Install with: pip install ${2}" >&2
        exit 2
    fi
}

mkdir -p "${EVIDENCE_DIR}"

# ---------------------------------------------------------------------------
# Pre-flight: confirm tools available
# ---------------------------------------------------------------------------
log "Pre-flight: checking required tools..."
require_tool pip_audit    "pip-audit>=2.7.3"
require_tool detect_secrets "detect-secrets>=1.4.0"
log "Tools OK."

# ---------------------------------------------------------------------------
# VER-015 — SCA gate dry-run
# ---------------------------------------------------------------------------
log "=== VER-015: SCA gate dry-run (pip-audit on vulnerable fixture) ==="

SCA_EXIT=0
SCA_OUTPUT_FILE="${EVIDENCE_DIR}/ver-015-sca-raw.json"

set +e
python -m pip_audit \
    --requirement "${VULN_REQ}" \
    --strict \
    --output json \
    --no-deps \
    > "${SCA_OUTPUT_FILE}" 2>"${EVIDENCE_DIR}/ver-015-sca-stderr.txt"
SCA_EXIT=$?
set -e

log "pip-audit exit code: ${SCA_EXIT}"

if [ "${SCA_EXIT}" -eq 0 ]; then
    fail "VER-015: pip-audit returned 0 (CLEAN) on a fixture with known-CVE packages."
    fail "The SCA gate is BROKEN — it would not block real vulnerabilities."
    SCA_VERDICT="GATE_FAILURE"
    OVERALL_PASS=$((OVERALL_PASS + 1))
else
    pass "VER-015: pip-audit correctly exited ${SCA_EXIT} on vulnerable fixture (BLOCKED)."
    SCA_VERDICT="BLOCKED"
fi

# Write structured evidence
python - <<PYEOF
import json, pathlib
ev = {
    "criterion": "VER-015",
    "gate": "sca",
    "tool": "pip-audit",
    "fixture": "tests/fixtures/requirements-vulnerable.txt",
    "exit_code": ${SCA_EXIT},
    "verdict": "${SCA_VERDICT}",
    "timestamp": "${TIMESTAMP}",
    "raw_output_file": "tests/evidence/ver-015-sca-raw.json",
}
out = pathlib.Path("${EVIDENCE_DIR}/ver-015-evidence.json")
out.write_text(json.dumps(ev, indent=2))
print(f"Evidence written: {out}")
PYEOF

# ---------------------------------------------------------------------------
# VER-018 — Secret-scan gate dry-run
# ---------------------------------------------------------------------------
log "=== VER-018: Secret-scan gate dry-run (detect-secrets on secrets fixture) ==="

SECRET_SCAN_FILE="${EVIDENCE_DIR}/ver-018-raw-scan.json"

python -m detect_secrets scan "${SECRETS_FX}" > "${SECRET_SCAN_FILE}"

FINDINGS=$(python - <<PYEOF
import json, sys
data = json.loads(open("${SECRET_SCAN_FILE}").read())
results = data.get("results", {})
total = sum(len(v) for v in results.values())
print(total)
PYEOF
)

log "detect-secrets findings count: ${FINDINGS}"

if [ "${FINDINGS}" -eq 0 ]; then
    fail "VER-018: detect-secrets found ZERO secrets in the fixture file."
    fail "The secret-scanning gate is BROKEN — it would not block hardcoded credentials."
    SECRET_VERDICT="GATE_FAILURE"
    OVERALL_PASS=$((OVERALL_PASS + 1))
else
    pass "VER-018: detect-secrets found ${FINDINGS} secret(s) in fixture (BLOCKED)."
    SECRET_VERDICT="BLOCKED"
fi

# Write structured evidence
python - <<PYEOF
import json, pathlib
raw = json.loads(open("${SECRET_SCAN_FILE}").read())
results = raw.get("results", {})
total = sum(len(v) for v in results.values())
ev = {
    "criterion": "VER-018",
    "gate": "secret-scan",
    "tool": "detect-secrets",
    "fixture": "tests/fixtures/secrets_fixture.py",
    "findings_count": total,
    "findings": results,
    "verdict": "${SECRET_VERDICT}",
    "timestamp": "${TIMESTAMP}",
    "raw_output_file": "tests/evidence/ver-018-raw-scan.json",
}
out = pathlib.Path("${EVIDENCE_DIR}/ver-018-evidence.json")
out.write_text(json.dumps(ev, indent=2))
print(f"Evidence written: {out}")
PYEOF

# ---------------------------------------------------------------------------
# Combined summary
# ---------------------------------------------------------------------------
python - <<PYEOF
import json, pathlib
summary = {
    "phase": "PHASE-007",
    "task": "TASK-012",
    "timestamp": "${TIMESTAMP}",
    "gates": {
        "VER-015": {
            "verdict": "${SCA_VERDICT}",
            "exit_code": ${SCA_EXIT},
            "evidence": "tests/evidence/ver-015-evidence.json",
        },
        "VER-018": {
            "verdict": "${SECRET_VERDICT}",
            "findings_count": ${FINDINGS},
            "evidence": "tests/evidence/ver-018-evidence.json",
        },
    },
    "overall": "PASS" if ${OVERALL_PASS} == 0 else "FAIL",
}
out = pathlib.Path("${EVIDENCE_DIR}/capture-summary.json")
out.write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
PYEOF

# ---------------------------------------------------------------------------
# Final exit
# ---------------------------------------------------------------------------
log "=== Summary ==="
if [ "${OVERALL_PASS}" -gt 0 ]; then
    fail "${OVERALL_PASS} gate(s) FAILED to block. Pipeline security is BROKEN."
    exit 1
fi

pass "All security gates correctly blocked the test fixtures."
pass "Evidence written to: ${EVIDENCE_DIR}/"
exit 0
