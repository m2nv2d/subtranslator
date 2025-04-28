import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from translator import init_genai_client, GenAIClientInitError
from core.config import get_settings

def main():
    """Loads config, initializes Gemini client, and prints the result."""
    
    try:
        settings = get_settings()
        print("Configuration loaded successfully.")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return
    
    try:
        client = init_genai_client(settings)
        print("Gemini client initialized successfully.\nTesting with a greeting...")
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
