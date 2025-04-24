from google import genai

from .exceptions import GenAIClientInitError
from .models import Config


def init_genai_client(config: Config) -> genai.client.Client:
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