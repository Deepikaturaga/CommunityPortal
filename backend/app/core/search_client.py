"""OpenSearch / Elasticsearch client adapter.

Wraps opensearch-py behind an injectable interface so tests can substitute
a deterministic double without hitting a real cluster.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from opensearchpy import AsyncOpenSearch

from app.core.config import settings


@runtime_checkable
class SearchClientProtocol(Protocol):
    """Minimal interface consumed by the search service and reconciler."""

    async def index(
        self,
        *,
        index: str,
        id: str,
        body: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def bulk(
        self,
        *,
        body: list[dict[str, Any]],
        index: str | None = None,
    ) -> dict[str, Any]: ...

    async def delete(
        self,
        *,
        index: str,
        id: str,
        ignore: list[int] | None = None,
    ) -> dict[str, Any]: ...

    async def search(
        self,
        *,
        index: str,
        body: dict[str, Any],
        size: int = 10,
        scroll: str | None = None,
    ) -> dict[str, Any]: ...

    async def scroll(
        self,
        *,
        scroll_id: str,
        scroll: str,
    ) -> dict[str, Any]: ...

    async def clear_scroll(self, *, scroll_id: str) -> dict[str, Any]: ...

    async def count(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def delete_by_query(
        self,
        *,
        index: str,
        body: dict[str, Any],
    ) -> dict[str, Any]: ...

    async def indices_exists(self, *, index: str) -> bool: ...

    async def indices_create(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...


class OpenSearchAdapter:
    """Production adapter backed by opensearch-py AsyncOpenSearch."""

    def __init__(self, client: AsyncOpenSearch) -> None:
        self._client = client

    @classmethod
    def from_settings(cls) -> "OpenSearchAdapter":
        host = str(settings.search_host)
        client = AsyncOpenSearch(
            hosts=[host],
            http_auth=(
                settings.search_username,
                settings.search_password.get_secret_value(),
            ),
            use_ssl=settings.search_use_ssl,
            verify_certs=settings.search_verify_certs,
            ssl_show_warn=False,
        )
        return cls(client)

    async def index(
        self,
        *,
        index: str,
        id: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._client.index(index=index, id=id, body=body)  # type: ignore[no-any-return]

    async def bulk(
        self,
        *,
        body: list[dict[str, Any]],
        index: str | None = None,
    ) -> dict[str, Any]:
        return await self._client.bulk(body=body, index=index)  # type: ignore[no-any-return]

    async def delete(
        self,
        *,
        index: str,
        id: str,
        ignore: list[int] | None = None,
    ) -> dict[str, Any]:
        return await self._client.delete(  # type: ignore[no-any-return]
            index=index, id=id, ignore=ignore or []
        )

    async def search(
        self,
        *,
        index: str,
        body: dict[str, Any],
        size: int = 10,
        scroll: str | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"index": index, "body": body, "size": size}
        if scroll:
            kwargs["scroll"] = scroll
        return await self._client.search(**kwargs)  # type: ignore[no-any-return]

    async def scroll(
        self,
        *,
        scroll_id: str,
        scroll: str,
    ) -> dict[str, Any]:
        return await self._client.scroll(scroll_id=scroll_id, scroll=scroll)  # type: ignore[no-any-return]

    async def clear_scroll(self, *, scroll_id: str) -> dict[str, Any]:
        return await self._client.clear_scroll(scroll_id=scroll_id)  # type: ignore[no-any-return]

    async def count(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._client.count(index=index, body=body or {})  # type: ignore[no-any-return]

    async def delete_by_query(
        self,
        *,
        index: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._client.delete_by_query(index=index, body=body)  # type: ignore[no-any-return]

    async def indices_exists(self, *, index: str) -> bool:
        return await self._client.indices.exists(index=index)  # type: ignore[no-any-return]

    async def indices_create(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._client.indices.create(index=index, body=body or {})  # type: ignore[no-any-return]

    async def close(self) -> None:
        await self._client.close()


# ── Application-singleton ─────────────────────────────────────────────────────
_search_client: OpenSearchAdapter | None = None


def get_search_client() -> OpenSearchAdapter:
    global _search_client
    if _search_client is None:
        _search_client = OpenSearchAdapter.from_settings()
    return _search_client


async def close_search_client() -> None:
    global _search_client
    if _search_client is not None:
        await _search_client.close()
        _search_client = None
