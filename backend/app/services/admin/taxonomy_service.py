"""Service layer for taxonomy (categories + tags).

Business rules enforced here (not in routers):
- Slugs are globally unique per type; duplicate slug → 409.
- Archived items cannot be assigned to NEW content (AC-028.2).
- Archive/restore transitions update status; existing content relations are untouched (RESTRICT FK).
- Deleting a category/tag with existing content associations is refused (FK RESTRICT).
- Parent category must exist and must not be the category itself.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.taxonomy import Category, Tag, TaxonomyStatus
from app.schemas.taxonomy_schemas import (
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
)


# ---------------------------------------------------------------------------
# Shared exceptions (mapped to HTTP codes in routers)
# ---------------------------------------------------------------------------


class NotFoundError(Exception):
    def __init__(self, entity: str, identifier: str | int) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} '{identifier}' not found.")


class ConflictError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class TaxonomyValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class ArchivedError(Exception):
    """Raised when trying to use an archived taxonomy item for new content (AC-028.2)."""

    def __init__(self, entity: str, identifier: str | int) -> None:
        self.entity = entity
        self.identifier = identifier
        super().__init__(
            f"{entity} '{identifier}' is archived and cannot be assigned to new content."
        )


# ---------------------------------------------------------------------------
# Category service
# ---------------------------------------------------------------------------


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ---- helpers ----

    async def _get_or_raise(self, category_id: int) -> Category:
        result = await self._db.execute(select(Category).where(Category.id == category_id))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Category", category_id)
        return obj

    async def _assert_slug_free(self, slug: str, exclude_id: int | None = None) -> None:
        stmt = select(Category.id).where(Category.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        exists = (await self._db.execute(stmt)).scalar_one_or_none()
        if exists is not None:
            raise ConflictError(f"Category slug '{slug}' is already taken.")

    async def _assert_parent_valid(self, parent_id: int, current_id: int | None = None) -> None:
        if current_id is not None and parent_id == current_id:
            raise TaxonomyValidationError("A category cannot be its own parent.")
        result = await self._db.execute(select(Category.id).where(Category.id == parent_id))
        if result.scalar_one_or_none() is None:
            raise NotFoundError("Category (parent)", parent_id)

    # ---- public API ----

    async def list_categories(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: TaxonomyStatus | None = None,
    ) -> tuple[list[Category], int]:
        stmt = select(Category)
        if status_filter is not None:
            stmt = stmt.where(Category.status == status_filter)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = (
            stmt.order_by(Category.sort_order, Category.label)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._db.execute(stmt)).scalars().all())
        return items, total

    async def get_category(self, category_id: int) -> Category:
        return await self._get_or_raise(category_id)

    async def get_category_by_slug(self, slug: str) -> Category:
        result = await self._db.execute(select(Category).where(Category.slug == slug))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Category", slug)
        return obj

    async def create_category(self, payload: CategoryCreate) -> Category:
        await self._assert_slug_free(payload.slug)
        if payload.parent_id is not None:
            await self._assert_parent_valid(payload.parent_id)
        obj = Category(
            slug=payload.slug,
            label=payload.label,
            description=payload.description,
            parent_id=payload.parent_id,
            sort_order=payload.sort_order,
            status=TaxonomyStatus.active,
        )
        self._db.add(obj)
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Category could not be created: {exc.orig}") from exc
        return obj

    async def update_category(self, category_id: int, payload: CategoryUpdate) -> Category:
        obj = await self._get_or_raise(category_id)
        if payload.label is not None:
            obj.label = payload.label
        if payload.description is not None:
            obj.description = payload.description
        if "parent_id" in payload.model_fields_set:
            if payload.parent_id is not None:
                await self._assert_parent_valid(payload.parent_id, current_id=category_id)
            obj.parent_id = payload.parent_id
        if payload.sort_order is not None:
            obj.sort_order = payload.sort_order
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Category could not be updated: {exc.orig}") from exc
        return obj

    async def archive_category(self, category_id: int) -> Category:
        obj = await self._get_or_raise(category_id)
        if obj.is_archived:
            return obj  # idempotent
        obj.archive()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def restore_category(self, category_id: int) -> Category:
        obj = await self._get_or_raise(category_id)
        if not obj.is_archived:
            return obj  # idempotent
        obj.restore()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def delete_category(self, category_id: int) -> None:
        """Hard delete — refused by DB if content associations exist (FK RESTRICT)."""
        obj = await self._get_or_raise(category_id)
        try:
            await self._db.delete(obj)
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                "Category cannot be deleted because it is referenced by existing content. "
                "Archive it instead."
            ) from exc

    # ---- AC-028.2 guard (called by content assignment code) ----

    async def assert_assignable(self, category_id: int) -> None:
        """Raise ArchivedError if the category is not active."""
        obj = await self._get_or_raise(category_id)
        if obj.is_archived:
            raise ArchivedError("Category", category_id)


# ---------------------------------------------------------------------------
# Tag service
# ---------------------------------------------------------------------------


class TagService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ---- helpers ----

    async def _get_or_raise(self, tag_id: int) -> Tag:
        result = await self._db.execute(select(Tag).where(Tag.id == tag_id))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Tag", tag_id)
        return obj

    async def _assert_slug_free(self, slug: str, exclude_id: int | None = None) -> None:
        stmt = select(Tag.id).where(Tag.slug == slug)
        if exclude_id is not None:
            stmt = stmt.where(Tag.id != exclude_id)
        exists = (await self._db.execute(stmt)).scalar_one_or_none()
        if exists is not None:
            raise ConflictError(f"Tag slug '{slug}' is already taken.")

    # ---- public API ----

    async def list_tags(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: TaxonomyStatus | None = None,
    ) -> tuple[list[Tag], int]:
        stmt = select(Tag)
        if status_filter is not None:
            stmt = stmt.where(Tag.status == status_filter)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total: int = (await self._db.execute(count_stmt)).scalar_one()
        stmt = stmt.order_by(Tag.label).offset((page - 1) * page_size).limit(page_size)
        items = list((await self._db.execute(stmt)).scalars().all())
        return items, total

    async def get_tag(self, tag_id: int) -> Tag:
        return await self._get_or_raise(tag_id)

    async def get_tag_by_slug(self, slug: str) -> Tag:
        result = await self._db.execute(select(Tag).where(Tag.slug == slug))
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("Tag", slug)
        return obj

    async def create_tag(self, payload: TagCreate) -> Tag:
        await self._assert_slug_free(payload.slug)
        obj = Tag(
            slug=payload.slug,
            label=payload.label,
            description=payload.description,
            status=TaxonomyStatus.active,
        )
        self._db.add(obj)
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Tag could not be created: {exc.orig}") from exc
        return obj

    async def update_tag(self, tag_id: int, payload: TagUpdate) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if payload.label is not None:
            obj.label = payload.label
        if payload.description is not None:
            obj.description = payload.description
        try:
            await self._db.commit()
            await self._db.refresh(obj)
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(f"Tag could not be updated: {exc.orig}") from exc
        return obj

    async def archive_tag(self, tag_id: int) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if obj.is_archived:
            return obj
        obj.archive()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def restore_tag(self, tag_id: int) -> Tag:
        obj = await self._get_or_raise(tag_id)
        if not obj.is_archived:
            return obj
        obj.restore()
        await self._db.commit()
        await self._db.refresh(obj)
        return obj

    async def delete_tag(self, tag_id: int) -> None:
        obj = await self._get_or_raise(tag_id)
        try:
            await self._db.delete(obj)
            await self._db.commit()
        except IntegrityError as exc:
            await self._db.rollback()
            raise ConflictError(
                "Tag cannot be deleted because it is referenced by existing content. "
                "Archive it instead."
            ) from exc

    # ---- AC-028.2 guard ----

    async def assert_assignable(self, tag_id: int) -> None:
        obj = await self._get_or_raise(tag_id)
        if obj.is_archived:
            raise ArchivedError("Tag", tag_id)
