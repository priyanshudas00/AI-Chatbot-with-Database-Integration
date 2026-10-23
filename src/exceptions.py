class AppError(Exception):
    """Base application exception."""


class DatabaseError(AppError):
    """Raised when database operations fail."""


class ApiError(AppError):
    """Raised when LLM API operations fail."""


class RateLimitError(ApiError):
    """Raised when LLM provider rate limits requests."""
