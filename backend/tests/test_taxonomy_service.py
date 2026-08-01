"""Unit tests for CategoryService and TagService.

Tests run against in-memory SQLite via the db_session fixture.
No HTTP layer involved — tests service methods directly.

Coverage:
  - Create (slug dedup, parent validation)
  - Update (PATCH semantics, circular parent prevention)
  - Archive / restore (idempotent, AC-028.2 guard)
  - List (status filter, pagination)
  - Delete (FK constraint enforcement)
  - assert_assignable (core of AC-028.2)
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.taxonomy import TaxonomyStatus
from app.schemas.taxonomy_schemas import (
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
)
from app.services.admin.taxonomy_service import (
    ArchivedError,
    CategoryService,
    ConflictError,
    NotFoundError,
    TagService,
    TaxonomyValidationError,
)


# ---------------------------------------------------------------------------
# Category service unit tests
# ---------------------------------------------------------------------------


class TestCategoryServiceCreate:
    async def test_create_returns_active_category(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="science", label="Science"))
        assert cat.id is not None
        assert cat.slug == "science"
        assert cat.status == TaxonomyStatus.active

    async def test_create_duplicate_slug_raises_conflict(self, db_session) -> None:
        svc = CategoryService(db_session)
        await svc.create_category(CategoryCreate(slug="tech", label="Tech"))
        with pytest.raises(ConflictError):
            await svc.create_category(CategoryCreate(slug="tech", label="Tech 2"))

    async def test_create_with_valid_parent(self, db_session) -> None:
        svc = CategoryService(db_session)
        parent = await svc.create_category(CategoryCreate(slug="parent", label="Parent"))
        child = await svc.create_category(
            CategoryCreate(slug="child", label="Child", parent_id=parent.id)
        )
        assert child.parent_id == parent.id

    async def test_create_invalid_parent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.create_category(
                CategoryCreate(slug="orphan", label="Orphan", parent_id=9999)
            )


class TestCategoryServiceUpdate:
    async def test_update_label(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="upd", label="Original"))
        updated = await svc.update_category(cat.id, CategoryUpdate(label="Updated"))
        assert updated.label == "Updated"

    async def test_update_self_parent_raises_validation_error(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="loop", label="Loop"))
        with pytest.raises(TaxonomyValidationError):
            await svc.update_category(cat.id, CategoryUpdate(parent_id=cat.id))

    async def test_update_nonexistent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_category(9999, CategoryUpdate(label="Ghost"))


class TestCategoryServiceArchive:
    async def test_archive_sets_status(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="arch-me", label="Archive Me"))
        archived = await svc.archive_category(cat.id)
        assert archived.status == TaxonomyStatus.archived

    async def test_archive_is_idempotent(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="idem", label="Idempotent"))
        await svc.archive_category(cat.id)
        # Second call should not raise
        again = await svc.archive_category(cat.id)
        assert again.status == TaxonomyStatus.archived

    async def test_restore_sets_active(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="restore-me", label="Restore Me"))
        await svc.archive_category(cat.id)
        restored = await svc.restore_category(cat.id)
        assert restored.status == TaxonomyStatus.active

    async def test_restore_is_idempotent(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="idem-r", label="Idempotent R"))
        # Never archived — restore should be a no-op
        result = await svc.restore_category(cat.id)
        assert result.status == TaxonomyStatus.active

    # AC-028.2: archived category must not be assignable to new content
    async def test_assert_assignable_archived_raises(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="no-assign", label="No Assign"))
        await svc.archive_category(cat.id)
        with pytest.raises(ArchivedError):
            await svc.assert_assignable(cat.id)

    async def test_assert_assignable_active_passes(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="yes-assign", label="Yes Assign"))
        # Should not raise
        await svc.assert_assignable(cat.id)


class TestCategoryServiceList:
    async def test_list_all(self, db_session) -> None:
        svc = CategoryService(db_session)
        await svc.create_category(CategoryCreate(slug="a", label="A"))
        await svc.create_category(CategoryCreate(slug="b", label="B"))
        items, total = await svc.list_categories()
        assert total == 2
        assert len(items) == 2

    async def test_list_filter_active(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="c", label="C"))
        await svc.create_category(CategoryCreate(slug="d", label="D"))
        await svc.archive_category(cat.id)
        items, total = await svc.list_categories(status_filter=TaxonomyStatus.active)
        assert total == 1
        assert items[0].slug == "d"

    async def test_list_filter_archived(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="e", label="E"))
        await svc.create_category(CategoryCreate(slug="f", label="F"))
        await svc.archive_category(cat.id)
        items, total = await svc.list_categories(status_filter=TaxonomyStatus.archived)
        assert total == 1
        assert items[0].slug == "e"

    async def test_pagination(self, db_session) -> None:
        svc = CategoryService(db_session)
        for i in range(5):
            await svc.create_category(CategoryCreate(slug=f"pg-{i}", label=f"PG {i}"))
        items, total = await svc.list_categories(page=1, page_size=3)
        assert total == 5
        assert len(items) == 3
        items2, _ = await svc.list_categories(page=2, page_size=3)
        assert len(items2) == 2


class TestCategoryServiceDelete:
    async def test_delete_removes_category(self, db_session) -> None:
        svc = CategoryService(db_session)
        cat = await svc.create_category(CategoryCreate(slug="del-me", label="Del Me"))
        await svc.delete_category(cat.id)
        with pytest.raises(NotFoundError):
            await svc.get_category(cat.id)

    async def test_delete_nonexistent_raises_not_found(self, db_session) -> None:
        svc = CategoryService(db_session)
        with pytest.raises(NotFoundError):
            await svc.delete_category(9999)


# ---------------------------------------------------------------------------
# Tag service unit tests
# ---------------------------------------------------------------------------


class TestTagServiceCreate:
    async def test_create_returns_active_tag(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="python", label="Python"))
        assert tag.id is not None
        assert tag.status == TaxonomyStatus.active

    async def test_create_duplicate_slug_raises_conflict(self, db_session) -> None:
        svc = TagService(db_session)
        await svc.create_tag(TagCreate(slug="dup", label="Dup"))
        with pytest.raises(ConflictError):
            await svc.create_tag(TagCreate(slug="dup", label="Dup 2"))


class TestTagServiceArchive:
    async def test_archive_sets_status(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="old-tag", label="Old Tag"))
        archived = await svc.archive_tag(tag.id)
        assert archived.status == TaxonomyStatus.archived

    async def test_restore_sets_active(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="restore-tag", label="Restore Tag"))
        await svc.archive_tag(tag.id)
        restored = await svc.restore_tag(tag.id)
        assert restored.status == TaxonomyStatus.active

    # AC-028.2
    async def test_assert_assignable_archived_raises(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="no-tag", label="No Tag"))
        await svc.archive_tag(tag.id)
        with pytest.raises(ArchivedError):
            await svc.assert_assignable(tag.id)

    async def test_assert_assignable_active_passes(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="yes-tag", label="Yes Tag"))
        await svc.assert_assignable(tag.id)


class TestTagServiceUpdate:
    async def test_update_label(self, db_session) -> None:
        svc = TagService(db_session)
        tag = await svc.create_tag(TagCreate(slug="upd-tag", label="Before"))
        updated = await svc.update_tag(tag.id, TagUpdate(label="After"))
        assert updated.label == "After"

    async def test_update_nonexistent_raises_not_found(self, db_session) -> None:
        svc = TagService(db_session)
        with pytest.raises(NotFoundError):
            await svc.update_tag(9999, TagUpdate(label="Ghost"))
