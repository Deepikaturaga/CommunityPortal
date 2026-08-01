"""
Minimal router-registration snippet produced by PHASE-031.

In the real repo this should be merged into backend/app/main.py by applying
the unified diff below rather than replacing the whole file.

Diff to apply
=============

--- a/backend/app/main.py
+++ b/backend/app/main.py
@@ -n,n @@
+from app.api.routes import kb_revisions
+
 # … after existing include_router calls …
+app.include_router(kb_revisions.router, prefix="/api/v1")

The router is registered under /api/v1/kb/articles/{article_id}/revisions
"""
