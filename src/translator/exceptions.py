class ConfigError(Exception):
    """Raised when configuration loading fails."""
    pass

class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ParsingError(Exception):
    """Raised when parsing of a file fails."""
    pass

class ContextDetectionError(Exception):
    """Raised when context detection fails."""
    pass

class ChunkTranslationError(Exception):
    """Raised when translation of a chunk fails."""
    pass

class GenAIClientInitError(Exception):
    """Raised when GenAI client initialization fails."""
    pass

class GenAIRequestError(Exception):
    """Raised when a GenAI request fails."""
    pass

class GenAIParsingError(Exception):
    """Raised when parsing of a GenAI response fails."""
    pass
