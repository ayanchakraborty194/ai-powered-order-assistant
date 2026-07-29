class AppError(Exception):
    """Base application error with HTTP status and error code."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        """Initialize AppError with a message.

        Args:
            message: Human-readable error description.
        """
        super().__init__(message)
        self.message = message

    def to_response_content(self, path: str) -> dict:
        """Build the JSON body for this error (used by handlers).

        Args:
            path: Request path for the response.

        Returns:
            Dict with error code, message, and path.
        """
        return {
            "error": {"code": self.code, "message": self.message},
            "path": path,
        }


class ValidationError(AppError):
    """Domain or request validation failed (e.g. unsafe/invalid generated SQL)."""

    status_code = 422
    code = "validation_error"


class InternalError(AppError):
    """Unexpected internal error (e.g. DB, LLM, or execution failure)."""

    status_code = 500
    code = "internal_error"
