"""Email delivery adapter -- SMTP or AWS SES, with a dev-mode skip flag."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.core.config import get_settings

# boto3 is declared as a runtime dependency in pyproject.toml.
# Imported at module level so tests can patch ``app.services.email.boto3``
# as a named module attribute.  The try/except handles environments where the
# package is intentionally omitted (SMTP-only installs).
try:
    import boto3
except ModuleNotFoundError:  # pragma: no cover
    boto3 = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def send_verification_email(to_email: str, token: str) -> None:
    """
    Send a verification email containing *token* to *to_email*.

    Dispatches via AWS SES when ``settings.email_provider == "ses"``,
    otherwise falls back to SMTP (starttls).

    When ``settings.email_skip_send`` is True (default in dev/test) the call
    is a no-op and the token is logged at DEBUG level only -- never logged at
    INFO+ in production to avoid leaking tokens to log pipelines.
    """
    settings = get_settings()

    if settings.email_skip_send:
        logger.debug(
            "Email send skipped (email_skip_send=true). "
            "token omitted from logs in production builds."
        )
        return

    if settings.email_provider == "ses":
        _send_via_ses(to_email, token, settings)
    else:
        _send_via_smtp(to_email, token, settings)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_mime_message(
    to_email: str,
    token: str,
    from_addr: str,
) -> MIMEMultipart:
    """Assemble a MIME multipart/alternative email for *token* delivery."""
    subject = "Please verify your email address"
    body_text = (
        f"Use the following token to verify your email address:\n\n{token}\n\n"
        "This token expires in 24 hours."
    )
    body_html = (
        "<html><body>"
        "<p>Thank you for registering.</p>"
        "<p>Please verify your email address using the token below:</p>"
        f"<pre>{token}</pre>"
        "<p>This token expires in 24 hours.</p>"
        "</body></html>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))
    return msg


def _send_via_smtp(to_email: str, token: str, settings: Any) -> None:  # noqa: ANN401
    """Dispatch via SMTP (starttls). Raises on failure -- caller decides fate."""
    msg = _build_mime_message(to_email, token, settings.smtp_from)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from, to_email, msg.as_string())
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        raise


def _send_via_ses(to_email: str, token: str, settings: Any) -> None:  # noqa: ANN401
    """
    Dispatch via AWS SES ``send_email`` API.

    Design notes
    ------------
    * Uses ``boto3.client("ses", region_name=settings.aws_region)`` so that
      AWS credential resolution follows the standard chain (IAM role,
      environment vars, ``~/.aws/credentials``).  No access-key is
      hard-coded or stored in application settings (AWS-only guardrail).
    * ``ses_from_arn`` is passed as ``SourceArn`` only when non-empty,
      supporting cross-account SES sending identities.
    * The call is synchronous; this function must only be invoked from a
      thread or non-async context (``email_skip_send=True`` guards CI paths).
    * A per-call client is created intentionally: the function is invoked
      infrequently (registration / resend only) and avoids shared mutable
      state across requests.

    Raises
    ------
    ``botocore.exceptions.ClientError`` on SES API errors. The caller
    (``issue_verification_token``) catches all exceptions, logs, and treats
    email failure as non-fatal so the token row is still persisted.
    """
    if boto3 is None:  # pragma: no cover
        raise RuntimeError(
            "boto3 is required when email_provider='ses'. "
            "Install it with: pip install boto3"
        )

    subject = "Please verify your email address"
    body_text = (
        f"Use the following token to verify your email address:\n\n{token}\n\n"
        "This token expires in 24 hours."
    )
    body_html = (
        "<html><body>"
        "<p>Thank you for registering.</p>"
        "<p>Please verify your email address using the token below:</p>"
        f"<pre>{token}</pre>"
        "<p>This token expires in 24 hours.</p>"
        "</body></html>"
    )

    ses = boto3.client("ses", region_name=settings.aws_region)

    kwargs: dict[str, Any] = {
        "Source": settings.smtp_from,
        "Destination": {"ToAddresses": [to_email]},
        "Message": {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": body_text, "Charset": "UTF-8"},
                "Html": {"Data": body_html, "Charset": "UTF-8"},
            },
        },
    }

    if settings.ses_from_arn:
        kwargs["SourceArn"] = settings.ses_from_arn

    try:
        ses.send_email(**kwargs)
    except Exception:
        logger.exception("SES send_email failed for recipient %s", to_email)
        raise
