"""Stage routers — each independently mountable for runtime isolation.

Imports for routers that have not yet been delivered are guarded with a
``try/except ImportError`` so that the discussion router (and its tests) can
be exercised in isolation without the full set of router modules present.
"""

from __future__ import annotations

# Always-present: discussion router is fully delivered
from .discussion_router import discussion_router

# Conditionally-present: other routers are delivered in separate phases.
# Guard each import so importing *this* package does not fail when the
# sibling modules are absent from the repository snapshot.
try:
    from .requirements import requirements_router
except ImportError:
    requirements_router = None  # type: ignore[assignment]

try:
    from .plan import plan_router
except ImportError:
    plan_router = None  # type: ignore[assignment]

try:
    from .design import design_router
except ImportError:
    design_router = None  # type: ignore[assignment]

try:
    from .task_breakdown import task_breakdown_router
except ImportError:
    task_breakdown_router = None  # type: ignore[assignment]

try:
    from .implementation import implementation_router
except ImportError:
    implementation_router = None  # type: ignore[assignment]

try:
    from .session import session_router
except ImportError:
    session_router = None  # type: ignore[assignment]

try:
    from .skills import skills_router
except ImportError:
    skills_router = None  # type: ignore[assignment]

try:
    from .metrics_api import metrics_router
except ImportError:
    metrics_router = None  # type: ignore[assignment]

try:
    from .billing import billing_router
except ImportError:
    billing_router = None  # type: ignore[assignment]

__all__ = [
    "requirements_router",
    "plan_router",
    "design_router",
    "task_breakdown_router",
    "implementation_router",
    "session_router",
    "skills_router",
    "metrics_router",
    "billing_router",
    "discussion_router",
]
