"""Re-export kb domain models from canonical location."""
from app.kb.article_models import Article, ArticleStatus

__all__ = ["Article", "ArticleStatus"]
