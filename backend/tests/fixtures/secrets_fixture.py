# ===========================================================================
# SECURITY GATE TEST FIXTURE — HARDCODED SECRET
# ===========================================================================
# PURPOSE
#   This file is a DELIBERATE TEST FIXTURE used by TASK-012 (PHASE-007) to
#   validate that the secret-scanning gate in CI correctly BLOCKS a commit
#   that contains a hardcoded credential.
#
# WHAT IT PROVES  (VER-018 evidence)
#   detect-secrets / gitleaks scanned this file, matched at least one high-
#   entropy string or known-pattern secret, and the "secret-scan-gate" job
#   exited non-zero — thereby blocking the pipeline.  Evidence is captured by
#   `capture_gate_evidence.sh` and attached to the CI run.
#
# IMPORTANT — THESE ARE NOT REAL CREDENTIALS
#   The strings below are synthetic values constructed to match common secret
#   patterns (AWS key format, JWT-looking token, generic password pattern).
#   They grant no access to any system.  They exist only to trigger scanners.
#
# DO NOT use this file outside the test fixtures directory.  It must never be
# imported by production code.  The CI job targets it by explicit path.
# ===========================================================================

# ---- AWS Access Key pattern (fake) ----------------------------------------
# Matches: r'AKIA[0-9A-Z]{16}'
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"  # noqa: S105
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # noqa: S105

# ---- Generic high-entropy password assignment (fake) ----------------------
DATABASE_PASSWORD = "Sup3rS3cr3tP@ssw0rd!ExampleOnly"  # noqa: S105

# ---- JWT-shaped token (fake) -----------------------------------------------
# Matches generic "token = <base64-ish long string>" heuristics
AUTH_TOKEN = (  # noqa: S105
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6OTk5OTk5OTk5OX0"
    ".EXAMPLEONLYFAKESIGNATURENOTREAL"
)

# ---- Private key PEM header (fake) -----------------------------------------
PRIVATE_KEY_PEM_HEADER = "-----BEGIN RSA PRIVATE KEY-----"  # noqa: S105


def intentionally_bad_function() -> None:  # pragma: no cover
    """
    This function intentionally demonstrates what NOT to do.
    It exists only so the file is valid Python and imports cleanly
    in the pytest fixture loader that verifies the fixture is present.
    Never call this from production code.
    """
    raise NotImplementedError(
        "This fixture function must never be called in production. "
        "It exists solely to validate secret-scanning CI gates."
    )
