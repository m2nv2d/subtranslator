class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ParsingError(Exception):
    """Raised when parsing of a file fails."""
    pass

class ContextDetectionError(Exception):
    """Raised when context detection fails."""
    pass

class SubtitleParsingError(Exception):
    """Raised when subtitle parsing fails."""
    pass