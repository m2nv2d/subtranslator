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
    from config_loader import load_config
    # Import Config for potential type checking or direct use later, though load_config handles instantiation
    from translator import Config
    print("Import successful.")
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}", file=sys.stderr)
    print("Please ensure:", file=sys.stderr)
    print(f"  1. The 'src' directory exists at: {project_root / 'src'}", file=sys.stderr)
    print(f"  2. 'src/config_loader.py' and 'src/models.py' exist.", file=sys.stderr)
    print(f"  3. You have necessary dependencies installed (e.g., python-dotenv). Try running `uv pip sync pyproject.toml` in {project_root}", file=sys.stderr)
    sys.exit(1)

print("\nAttempting to load configuration using load_config()...")

try:
    # Call the function to load configuration
    config: Config = load_config()

    # Print the loaded configuration object
    print("\n--- Loaded Configuration ---")
    print(config)
    print("--------------------------\n")
    print("Test script finished successfully.")

except SystemExit as e:
    # Catch the SystemExit raised by load_config if API key is missing
    print(f"\nERROR: Exiting due to configuration error detected by load_config: {e}", file=sys.stderr)
    sys.exit(1) # Propagate the exit
except Exception as e:
    print(f"\nERROR: An unexpected error occurred during configuration loading: {e}", file=sys.stderr)
    logging.exception("Traceback for unexpected error:") # Log the full traceback if logging is configured
    sys.exit(1)
