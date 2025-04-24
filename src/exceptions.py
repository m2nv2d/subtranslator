"""Custom exception classes for the application."""


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ParsingError(Exception):
    """Raised when parsing of a file fails."""
    pass
