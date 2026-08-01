"""Slug generation for KB articles."""
import re
import unicodedata


def slugify(text: str) -> str:
    """
    Convert *text* to a URL-safe ASCII slug.

    1. Normalise unicode to NFKD, encode as ASCII (ignore non-ASCII).
    2. Lower-case.
    3. Replace runs of non-alphanumeric characters with a single hyphen.
    4. Strip leading/trailing hyphens.
    """
    normalised = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    lowered = normalised.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "article"
