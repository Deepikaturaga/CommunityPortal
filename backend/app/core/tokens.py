"""Email-verification token helpers using itsdangerous URLSafeTimedSerializer."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

_SALT = "email-verification"


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().secret_key, salt=_SALT)


def generate_verification_token(email: str) -> str:
    """Generate a signed, time-limited token for *email*."""
    return _serializer().dumps(email)


def verify_verification_token(token: str) -> str | None:
    """
    Validate *token* and return the email address it encodes.

    Returns ``None`` if the token is invalid or expired.
    """
    ttl = get_settings().email_verification_token_ttl
    try:
        email: str = _serializer().loads(token, max_age=ttl)
        return email
    except (SignatureExpired, BadSignature):
        return None
