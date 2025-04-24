from google import genai

from .exceptions import GenAIClientInitError
from .models import Config

FAST_MODEL = "gemini-2.5-flash-preview-04-17"
NORMAL_MODEL = "gemini-2.5-pro-preview-03-25"

def init_genai_client(config: Config) -> genai.client.Client | None:
    """Initializes and returns a Google Generative AI client.

    Args:
        config: Configuration object containing the API key.

    Returns:
        An initialized GenAI client instance.

    Raises:
        GenAIClientInitError: If client initialization fails.
    """
    try:
        client = genai.Client(api_key=config.gemini_api_key)
        return client
    except Exception as e:
        raise GenAIClientInitError("Failed to initialize Gemini Client") from e