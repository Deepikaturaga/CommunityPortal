"""Locust load-test scaffolding for the posts service.

This file is NOT executed in the CI gate.  It provides a realistic load
scenario for manual performance validation against a running instance.

Target thresholds (indicative — tune per environment):
  - POST /api/v1/posts  p95 < 200 ms
  - GET  /api/v1/posts  p95 < 150 ms
  - GET  /api/v1/posts/{id}  p95 < 100 ms

Usage:
    locust -f tests/posts/locustfile.py --host http://localhost:8000
"""
from __future__ import annotations

import random
import string
import uuid
from typing import Any

try:
    from locust import HttpUser, between, task
except ImportError:  # pragma: no cover
    # Allow the file to be imported without locust installed (test collection).
    HttpUser = object  # type: ignore[misc,assignment]

    def between(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        return None

    def task(*args: Any, **kwargs: Any) -> Any:  # type: ignore[misc]
        def decorator(fn: Any) -> Any:
            return fn
        return decorator


_ALPHABET = string.ascii_letters + string.digits


def _rand_str(length: int = 10) -> str:
    return "".join(random.choices(_ALPHABET, k=length))


class PostsUser(HttpUser):
    """Simulates a mix of create / read / list / update / delete operations."""

    wait_time = between(0.1, 0.5)

    # JWT token injected at start; replace with real auth flow if needed.
    _token: str = ""
    _post_ids: list[str] = []

    def on_start(self) -> None:
        """Obtain an auth token before starting tasks."""
        # In a real environment call the token endpoint.
        # Here we use a placeholder — override with the actual auth URL.
        self._post_ids = []

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task(3)
    def create_post(self) -> None:
        resp = self.client.post(
            "/api/v1/posts",
            json={"title": f"Load post {_rand_str()}", "body": "body " * 20},
            headers=self._auth_headers,
            name="/api/v1/posts [POST]",
        )
        if resp.status_code == 201:
            self._post_ids.append(resp.json()["id"])

    @task(10)
    def list_posts(self) -> None:
        self.client.get(
            "/api/v1/posts?page_size=20",
            headers=self._auth_headers,
            name="/api/v1/posts [GET list]",
        )

    @task(8)
    def get_post(self) -> None:
        if not self._post_ids:
            return
        post_id = random.choice(self._post_ids)
        self.client.get(
            f"/api/v1/posts/{post_id}",
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [GET]",
        )

    @task(2)
    def update_post(self) -> None:
        if not self._post_ids:
            return
        post_id = random.choice(self._post_ids)
        self.client.patch(
            f"/api/v1/posts/{post_id}",
            json={"title": f"Updated {_rand_str()}"},
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [PATCH]",
        )

    @task(1)
    def delete_post(self) -> None:
        if not self._post_ids:
            return
        post_id = self._post_ids.pop()
        self.client.delete(
            f"/api/v1/posts/{post_id}",
            headers=self._auth_headers,
            name="/api/v1/posts/{id} [DELETE]",
        )
