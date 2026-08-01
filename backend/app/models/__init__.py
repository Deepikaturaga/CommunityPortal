# Import all models so SQLAlchemy metadata is populated
from app.models.user import User as User, UserRole as UserRole
from app.models.discussion import Discussion as Discussion, DiscussionStatus as DiscussionStatus
from app.models.post import Post as Post
from app.models.kb_article import KBArticle as KBArticle, ArticleStatus as ArticleStatus
from app.models.notification import Notification as Notification, NotificationKind as NotificationKind
from app.models.audit_log import AuditLog as AuditLog
