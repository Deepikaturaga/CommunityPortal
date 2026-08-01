"""
Tests for the KB article sanitizer (AC-022.3, VER-004).

These are pure unit tests — no DB or HTTP required.
"""
import pytest

from app.kb.sanitizer import sanitize_html


class TestSanitizeHtml:
    # -- Allowed content passes through ----------------------------------

    def test_plain_text_preserved(self) -> None:
        assert sanitize_html("Hello world") == "Hello world"

    def test_allowed_tags_preserved(self) -> None:
        html = "<p>Hello <strong>world</strong></p>"
        result = sanitize_html(html)
        assert "<p>" in result
        assert "<strong>" in result

    def test_allowed_link_preserved(self) -> None:
        html = '<a href="https://example.com" title="ex">link</a>'
        result = sanitize_html(html)
        assert 'href="https://example.com"' in result

    def test_img_with_safe_src_preserved(self) -> None:
        html = '<img src="https://cdn.example.com/img.png" alt="logo">'
        result = sanitize_html(html)
        assert 'src="https://cdn.example.com/img.png"' in result

    def test_heading_preserved(self) -> None:
        html = "<h2>Section</h2>"
        result = sanitize_html(html)
        assert "<h2>" in result

    def test_ordered_list_preserved(self) -> None:
        html = "<ol><li>first</li><li>second</li></ol>"
        result = sanitize_html(html)
        assert "<ol>" in result
        assert "<li>" in result

    def test_code_block_preserved(self) -> None:
        html = "<pre><code>print('hi')</code></pre>"
        result = sanitize_html(html)
        assert "<pre>" in result
        assert "<code>" in result

    # -- Dangerous content stripped --------------------------------------

    def test_script_tag_stripped(self) -> None:
        html = "<p>Hi</p><script>alert('xss')</script>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "alert" not in result

    def test_script_tag_strips_content_too(self) -> None:
        """bleach strip=True removes the tag AND its contents for script."""
        html = "<script>evil()</script>"
        result = sanitize_html(html)
        assert "evil" not in result

    def test_iframe_stripped(self) -> None:
        html = '<iframe src="https://evil.com"></iframe>'
        result = sanitize_html(html)
        assert "<iframe>" not in result

    def test_style_tag_stripped(self) -> None:
        html = "<style>body{display:none}</style>"
        result = sanitize_html(html)
        assert "<style>" not in result

    def test_on_event_attribute_stripped(self) -> None:
        html = '<p onclick="evil()">Click me</p>'
        result = sanitize_html(html)
        assert "onclick" not in result
        # Text content preserved
        assert "Click me" in result

    def test_javascript_href_stripped(self) -> None:
        html = '<a href="javascript:alert(1)">XSS</a>'
        result = sanitize_html(html)
        assert "javascript:" not in result
        # Link text preserved
        assert "XSS" in result

    def test_vbscript_href_stripped(self) -> None:
        html = '<a href="vbscript:MsgBox(1)">XSS</a>'
        result = sanitize_html(html)
        assert "vbscript:" not in result

    def test_data_uri_img_src_stripped(self) -> None:
        html = '<img src="data:text/html,<h1>XSS</h1>" alt="x">'
        result = sanitize_html(html)
        assert "data:" not in result

    def test_html_comments_stripped(self) -> None:
        html = "<!-- hidden comment --><p>visible</p>"
        result = sanitize_html(html)
        assert "<!--" not in result
        assert "visible" in result

    def test_object_embed_stripped(self) -> None:
        html = '<object data="evil.swf"></object>'
        result = sanitize_html(html)
        assert "<object>" not in result

    # -- Edge cases ------------------------------------------------------

    def test_empty_string(self) -> None:
        assert sanitize_html("") == ""

    def test_whitespace_only(self) -> None:
        result = sanitize_html("   ")
        assert result.strip() == ""

    def test_deeply_nested_xss(self) -> None:
        html = "<p><b><i><script>x()</script></i></b></p>"
        result = sanitize_html(html)
        assert "<script>" not in result
        assert "x()" not in result

    def test_unicode_content_preserved(self) -> None:
        html = "<p>Héllo wörld 日本語</p>"
        result = sanitize_html(html)
        assert "Héllo" in result
        assert "日本語" in result
