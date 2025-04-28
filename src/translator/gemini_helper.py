from google import genai

from translator.exceptions import GenAIClientInitError
from core.config import Settings

def init_genai_client(settings: Settings) -> genai.client.Client | None:
    """Initializes and returns a Google Generative AI client.

    Args:
        settings: Pydantic Settings object containing the API key.

    Returns:
        An initialized GenAI client instance.

    Raises:
        GenAIClientInitError: If client initialization fails.
    """
    try:
        client = genai.Client(api_key=settings.AI_API_KEY)
        return client
    except Exception as e:
        raise GenAIClientInitError("Failed to initialize Gemini Client") from e