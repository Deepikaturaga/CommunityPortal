from __future__ import annotations

from typing import Any

from opensearchpy import AsyncOpenSearch

from app.core.config import Settings, get_settings

# ── OpenSearch index mapping (STORE-007) ──────────────────────────────────────
#
# Only APPROVED items are indexed (AC-027.5).
# The mapping is declared here so it can be applied at bootstrap and referenced
# in tests.  Field choices:
#
#   - title / body: text with keyword sub-field for exact/sort queries.
#   - status: keyword (for filter queries, though only "approved" ever lands).
#   - author_id / entity_type: keyword (exact match / aggregation).
#   - version: integer (idempotency tracking in OpenSearch docs is secondary
#     to the DB ledger; kept for debugging).
#   - occurred_at: date (range queries / sorting).
#   - metadata: flat object (dynamic: false to avoid mapping explosion).

CONTENT_INDEX_MAPPING: dict[str, Any] = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "content_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                }
            }
        },
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "entity_id": {"type": "keyword"},
            "entity_type": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "content_analyzer",
                "fields": {"keyword": {"type": "keyword", "ignore_above": 512}},
            },
            "body": {"type": "text", "analyzer": "content_analyzer"},
            "author_id": {"type": "keyword"},
            "status": {"type": "keyword"},
            "version": {"type": "integer"},
            "occurred_at": {"type": "date"},
            "metadata": {"type": "object", "dynamic": False},
        },
    },
}

# Idempotency ledger index — lightweight, no full-text needed.
PROCESSED_EVENTS_INDEX_MAPPING: dict[str, Any] = {
    "settings": {"number_of_shards": 1, "number_of_replicas": 1},
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "entity_type": {"type": "keyword"},
            "entity_id": {"type": "keyword"},
            "version": {"type": "integer"},
            "event_type": {"type": "keyword"},
            "processed_at": {"type": "date"},
        },
    },
}


def build_opensearch_client(settings: Settings | None = None) -> AsyncOpenSearch:
    """Construct an AsyncOpenSearch client from application settings."""
    cfg = settings or get_settings()
    kwargs: dict[str, Any] = {
        "hosts": [cfg.opensearch_url],
        "use_ssl": cfg.opensearch_url.startswith("https://"),
        "verify_certs": cfg.opensearch_url.startswith("https://"),
        "timeout": 10,
        "max_retries": 3,
        "retry_on_timeout": True,
    }
    username = cfg.opensearch_username
    password = cfg.opensearch_password.get_secret_value()
    if username and password:
        kwargs["http_auth"] = (username, password)

    return AsyncOpenSearch(**kwargs)


async def ensure_indices(client: AsyncOpenSearch, settings: Settings | None = None) -> None:
    """Create indices with mapping if they do not already exist."""
    cfg = settings or get_settings()
    pairs = [
        (cfg.opensearch_index_content, CONTENT_INDEX_MAPPING),
        (cfg.opensearch_index_processed_events, PROCESSED_EVENTS_INDEX_MAPPING),
    ]
    for index_name, mapping in pairs:
        exists = await client.indices.exists(index=index_name)
        if not exists:
            await client.indices.create(index=index_name, body=mapping)
