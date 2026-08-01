from __future__ import annotations

"""Domain exceptions for the discussion/reply service.

Each exception maps to a specific HTTP status code via the global exception handler,
keeping the service layer free of FastAPI concerns.
"""


class DiscussionNotFoundError(Exception):
    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} not found.")


class DiscussionLockedError(Exception):
    """Raised when a reply is attempted on a locked discussion (AC-012)."""

    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} is locked and does not accept new replies.")


class DiscussionHiddenError(Exception):
    """Raised when a reply is attempted on a hidden discussion (AC-012)."""

    def __init__(self, discussion_id: int) -> None:
        self.discussion_id = discussion_id
        super().__init__(f"Discussion {discussion_id} is hidden.")


class ReplyNotFoundError(Exception):
    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Reply {reply_id} not found.")


class ReplyForbiddenError(Exception):
    """Raised when a user attempts to edit a reply they do not own (AC-013)."""

    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Not authorised to modify reply {reply_id}.")


class ReplyHiddenError(Exception):
    """Raised when editing a hidden reply is attempted."""

    def __init__(self, reply_id: int) -> None:
        self.reply_id = reply_id
        super().__init__(f"Reply {reply_id} is hidden and cannot be edited.")


class ReplyBodyTooShortError(Exception):
    def __init__(self, min_length: int) -> None:
        self.min_length = min_length
        super().__init__(f"Reply body must be at least {min_length} character(s).")


class ReplyBodyTooLongError(Exception):
    def __init__(self, max_length: int) -> None:
        self.max_length = max_length
        super().__init__(f"Reply body must not exceed {max_length} characters.")
