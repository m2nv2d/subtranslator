import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from translator import init_genai_client, Config, GenAIClientInitError

def main():
    """Loads config, initializes Gemini client, and prints the result."""
    print(f"Adding project root to sys.path: {project_root}")
    env_path = project_root / '.env'
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path)

    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print("Error: AI_API_KEY not found in environment variables or .env file.")
        print("Please create a .env file in the project root with AI_API_KEY=your_key")
        return

    # Create a dummy config for testing
    # Only the API key is needed for init_genai_client
    config = Config(
        ai_api_key=api_key,
        target_languages=["en"],  # Placeholder
        chunk_max_blocks=10,  # Placeholder
        retry_max_attempts=3, # Placeholder
        log_level="INFO" # Placeholder
    )

    print("Attempting to initialize Gemini client...")
    try:
        client = init_genai_client(config)
        print("Gemini client initialized successfully. Testing with a greeting...")
        response = client.models.generate_content(
            model='gemini-2.0-flash', contents='Hi'
        )
        print(response.text)
    except GenAIClientInitError as e:
        print(f"Error initializing Gemini client: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
