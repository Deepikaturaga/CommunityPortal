"""In-memory search client double for tests.

Implements SearchClientProtocol without hitting a real cluster.
Supports the full lifecycle used by SearchReconciler:
  - index / bulk (upsert)
  - search + scroll / clear_scroll
  - count
  - delete_by_query
  - delete
  - indices_exists / indices_create
"""

from __future__ import annotations

import copy
from typing import Any

from app.core.search_client import SearchClientProtocol


class InMemorySearchClient:
    """Deterministic in-memory search double.

    State is kept in ``self.indices``: a ``dict[index_name, dict[doc_id, body]]``.
    Call-counts are tracked in ``self.calls`` for assertion in tests.
    """

    def __init__(self) -> None:
        # index_name → {doc_id: payload}
        self.indices: dict[str, dict[str, dict[str, Any]]] = {}
        # counts of each operation
        self.calls: dict[str, int] = {
            "index": 0,
            "bulk": 0,
            "delete": 0,
            "search": 0,
            "scroll": 0,
            "clear_scroll": 0,
            "count": 0,
            "delete_by_query": 0,
            "indices_exists": 0,
            "indices_create": 0,
        }
        self._scroll_contexts: dict[str, list[dict[str, Any]]] = {}
        self._scroll_counter = 0

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ensure_index(self, name: str) -> None:
        if name not in self.indices:
            self.indices[name] = {}

    def doc_count(self, index: str) -> int:
        return len(self.indices.get(index, {}))

    def get_doc(self, index: str, doc_id: str) -> dict[str, Any] | None:
        return self.indices.get(index, {}).get(doc_id)

    def all_ids(self, index: str) -> set[str]:
        return set(self.indices.get(index, {}).keys())

    # ── protocol impl ────────────────────────────────────────────────────────

    async def index(
        self,
        *,
        index: str,
        id: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls["index"] += 1
        self._ensure_index(index)
        self.indices[index][id] = copy.deepcopy(body)
        return {"result": "created", "_id": id}

    async def bulk(
        self,
        *,
        body: list[dict[str, Any]],
        index: str | None = None,
    ) -> dict[str, Any]:
        self.calls["bulk"] += 1
        items: list[dict[str, Any]] = []
        i = 0
        while i < len(body):
            action_wrapper = body[i]
            i += 1

            if "index" in action_wrapper:
                meta = action_wrapper["index"]
                idx = meta.get("_index") or index or "default"
                doc_id = meta.get("_id", "")
                self._ensure_index(idx)
                doc_body: dict[str, Any] = body[i] if i < len(body) else {}
                i += 1
                self.indices[idx][doc_id] = copy.deepcopy(doc_body)
                items.append({"index": {"_id": doc_id, "result": "created", "status": 200}})

            elif "delete" in action_wrapper:
                meta = action_wrapper["delete"]
                idx = meta.get("_index") or index or "default"
                doc_id = meta.get("_id", "")
                self._ensure_index(idx)
                existed = doc_id in self.indices[idx]
                self.indices[idx].pop(doc_id, None)
                items.append(
                    {
                        "delete": {
                            "_id": doc_id,
                            "result": "deleted" if existed else "not_found",
                            "status": 200 if existed else 404,
                        }
                    }
                )

            elif "create" in action_wrapper:
                meta = action_wrapper["create"]
                idx = meta.get("_index") or index or "default"
                doc_id = meta.get("_id", "")
                self._ensure_index(idx)
                doc_body = body[i] if i < len(body) else {}
                i += 1
                self.indices[idx][doc_id] = copy.deepcopy(doc_body)
                items.append({"create": {"_id": doc_id, "result": "created", "status": 201}})

        return {"errors": False, "items": items}

    async def delete(
        self,
        *,
        index: str,
        id: str,
        ignore: list[int] | None = None,
    ) -> dict[str, Any]:
        self.calls["delete"] += 1
        self._ensure_index(index)
        existed = id in self.indices[index]
        self.indices[index].pop(id, None)
        return {"result": "deleted" if existed else "not_found"}

    async def search(
        self,
        *,
        index: str,
        body: dict[str, Any],
        size: int = 10,
        scroll: str | None = None,
    ) -> dict[str, Any]:
        self.calls["search"] += 1
        self._ensure_index(index)
        docs = list(self.indices[index].items())
        hits = [{"_id": did, "_source": copy.deepcopy(src)} for did, src in docs]
        page = hits[:size]
        remaining = hits[size:]

        scroll_id: str | None = None
        if scroll and remaining:
            self._scroll_counter += 1
            scroll_id = f"scroll_{self._scroll_counter}"
            self._scroll_contexts[scroll_id] = remaining

        return {
            "_scroll_id": scroll_id,
            "hits": {
                "total": {"value": len(hits)},
                "hits": page,
            },
        }

    async def scroll(
        self,
        *,
        scroll_id: str,
        scroll: str,
    ) -> dict[str, Any]:
        self.calls["scroll"] += 1
        remaining = self._scroll_contexts.pop(scroll_id, [])
        # Return one batch at a time
        page_size = 100
        page = remaining[:page_size]
        still_remaining = remaining[page_size:]
        new_scroll_id: str | None = None
        if still_remaining:
            self._scroll_counter += 1
            new_scroll_id = f"scroll_{self._scroll_counter}"
            self._scroll_contexts[new_scroll_id] = still_remaining
        return {
            "_scroll_id": new_scroll_id,
            "hits": {"total": {"value": len(remaining)}, "hits": page},
        }

    async def clear_scroll(self, *, scroll_id: str) -> dict[str, Any]:
        self.calls["clear_scroll"] += 1
        self._scroll_contexts.pop(scroll_id, None)
        return {"succeeded": True}

    async def count(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls["count"] += 1
        self._ensure_index(index)
        return {"count": len(self.indices[index])}

    async def delete_by_query(
        self,
        *,
        index: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        self.calls["delete_by_query"] += 1
        self._ensure_index(index)
        deleted_count = len(self.indices[index])
        self.indices[index] = {}
        return {"deleted": deleted_count}

    async def indices_exists(self, *, index: str) -> bool:
        self.calls["indices_exists"] += 1
        return index in self.indices

    async def indices_create(
        self,
        *,
        index: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls["indices_create"] += 1
        self._ensure_index(index)
        return {"acknowledged": True}

    async def close(self) -> None:
        pass


# Verify the double satisfies the protocol at import time.
assert isinstance(InMemorySearchClient(), SearchClientProtocol)
