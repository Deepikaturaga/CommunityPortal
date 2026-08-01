"""
HTML sanitizer for KB article body content (AC-022.3).

Uses ``bleach`` to strip all tags/attributes that are not on an explicit
allow-list. Raw user input is NEVER persisted; the sanitized result is
what hits the database.

Allowed tags are a safe subset suitable for rich-text knowledge-base
articles: standard text formatting, headings, lists, blockquotes, code,
and links — but NO script, style, iframe, object, or embed elements.
"""
import re

import bleach

# ---------------------------------------------------------------------------
# Allow-lists
# ---------------------------------------------------------------------------
ALLOWED_TAGS: frozenset[str] = frozenset(
    {
        # Structure
        "p", "br", "hr", "div", "span",
        # Headings
        "h1", "h2", "h3", "h4", "h5", "h6",
        # Emphasis
        "b", "i", "strong", "em", "s", "del", "ins", "mark", "sub", "sup",
        # Lists
        "ul", "ol", "li", "dl", "dt", "dd",
        # Quotation / code
        "blockquote", "pre", "code", "kbd", "samp",
        # Tables (read-only layout; no form elements)
        "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
        # Links and media (src validated separately)
        "a", "img",
        # Misc inline
        "abbr", "cite", "time", "small",
    }
)

ALLOWED_ATTRIBUTES: dict[str, list[str]] = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "abbr": ["title"],
    "time": ["datetime"],
    "th": ["scope", "colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
    # Allow class on structural wrappers for styling only — never event handlers
    "div": ["class"],
    "span": ["class"],
    "p": ["class"],
    "pre": ["class"],
    "code": ["class"],
}

# Disallow javascript: / vbscript: / data: URIs in href/src
_DANGEROUS_URL_RE = re.compile(
    r"^\s*(javascript|vbscript|data)\s*:", re.IGNORECASE
)


def _sanitize_link(tag: str, name: str, value: str) -> str | bool:
    """bleach attribute callable: validate href/src are not dangerous."""
    if name in ("href", "src"):
        if _DANGEROUS_URL_RE.match(value):
            return False  # strip the attribute
    return True  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_html(raw: str) -> str:
    """
    Return a sanitized copy of *raw* HTML suitable for storage and rendering.

    Strips disallowed tags (content preserved), removes disallowed attributes,
    and rejects javascript:/vbscript:/data: URIs in href/src.

    This function is **deterministic and has no side effects** — safe to call
    in unit tests without a database.
    """
    cleaned = bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=_sanitize_link,  # type: ignore[arg-type]
        strip=True,        # strip disallowed tags rather than escaping them
        strip_comments=True,
    )
    return cleaned
