"""Pydantic schema unit tests — VER-004 slug/label validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.taxonomy_schemas import CategoryCreate, CategoryUpdate, TagCreate, TagUpdate


class TestCategoryCreateSchema:
    def test_valid(self) -> None:
        c = CategoryCreate(slug="my-cat", label="My Cat")
        assert c.slug == "my-cat"
        assert c.sort_order == 0

    def test_slug_uppercase_normalised(self) -> None:
        # Validator lowercases
        c = CategoryCreate(slug="My-Cat", label="My Cat")
        assert c.slug == "my-cat"

    def test_slug_spaces_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="my cat", label="My Cat")

    def test_slug_underscore_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="my_cat", label="My Cat")

    def test_label_stripped(self) -> None:
        c = CategoryCreate(slug="s", label="  hello  ")
        assert c.label == "hello"

    def test_description_optional(self) -> None:
        c = CategoryCreate(slug="s2", label="S")
        assert c.description is None

    def test_sort_order_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="s3", label="S", sort_order=-1)

    def test_empty_slug_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryCreate(slug="", label="L")


class TestCategoryUpdateSchema:
    def test_valid_single_field(self) -> None:
        u = CategoryUpdate(label="New")
        assert u.label == "New"

    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate()

    def test_all_none_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CategoryUpdate(label=None, description=None, parent_id=None, sort_order=None)


class TestTagCreateSchema:
    def test_valid(self) -> None:
        t = TagCreate(slug="rust", label="Rust")
        assert t.slug == "rust"

    def test_slug_with_numbers(self) -> None:
        t = TagCreate(slug="python3", label="Python 3")
        assert t.slug == "python3"

    def test_invalid_slug_422(self) -> None:
        with pytest.raises(ValidationError):
            TagCreate(slug="C++", label="C++")


class TestTagUpdateSchema:
    def test_empty_update_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TagUpdate()
