import sys
from pathlib import Path
import logging

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

# Configure logging for the test script itself if needed
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s') # Optional: uncomment if script-specific logging needed

print(f"Project root added to sys.path: {project_root}")
print("Attempting to import from src...")

try:
    from core.config import get_settings, Settings
    print("Import successful.")
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}", file=sys.stderr)
    print("Please ensure:", file=sys.stderr)
    print(f"  1. The 'src' directory exists at: {project_root / 'src'}", file=sys.stderr)
    print(f"  2. 'src/core/config.py' exists.", file=sys.stderr)
    print(f"  3. You have necessary dependencies installed (e.g., pydantic-settings). Try running `uv pip sync pyproject.toml` in {project_root}", file=sys.stderr)
    sys.exit(1)

print("\nAttempting to load configuration using get_settings()...")

try:
    # Call the function to load configuration
    settings: Settings = get_settings()

    # Print the loaded configuration object
    print("\n--- Loaded Configuration ---")
    print(f"AI Provider: {settings.AI_PROVIDER}")
    print(f"API Key: {'[REDACTED]' if settings.AI_API_KEY else 'Not provided'}")
    print(f"Fast Model: {settings.FAST_MODEL}")
    print(f"Normal Model: {settings.NORMAL_MODEL}")
    print(f"Target Languages: {settings.TARGET_LANGUAGES}")
    print(f"Chunk Max Blocks: {settings.CHUNK_MAX_BLOCKS}")
    print(f"Retry Max Attempts: {settings.RETRY_MAX_ATTEMPTS}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print("--------------------------\n")
    print("Test script finished successfully.")

except Exception as e:
    print(f"\nERROR: An unexpected error occurred during configuration loading: {e}", file=sys.stderr)
    logging.exception("Traceback for unexpected error:") # Log the full traceback if logging is configured
    sys.exit(1)
