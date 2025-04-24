import argparse
import logging
import sys
from pathlib import Path
import os

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.config_loader import load_config
from src.context_detector import detect_context
from src.exceptions import ContextDetectionError, ParsingError
from src.parser import parse_srt
from src.gemini_helper import init_genai_client

# Basic logging setup for the script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Debug script for context_detector.")
    parser.add_argument("srt_path", help="Path to the input SRT file.")
    parser.add_argument(
        "speed_mode",
        choices=["mock", "fast", "normal"],
        help="Speed mode for context detection ('mock', 'fast', 'normal')."
    )
    args = parser.parse_args()

    logger.info(f"Starting debug script for {args.srt_path} with mode '{args.speed_mode}'...")

    try:
        # 1. Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        # Optionally override log level from config if needed
        # logging.getLogger().setLevel(config.log_level.upper())

        # Initialize GenAI client only if needed
        genai_client = None
        if args.speed_mode != "mock":
            logger.info("Initializing GenAI client...")
            try:
                genai_client = init_genai_client(config)
                logger.info("GenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}. Proceeding without client for context detection.")
                # Depending on requirements, you might want to exit here for non-mock modes
                # sys.exit(1)

        # === Check if SRT file exists ===
        if not os.path.exists(args.srt_path):
            logger.error(f"Error: SRT file not found at {args.srt_path}")
            sys.exit(1)

        # 2. Parse the SRT file
        logger.info(f"Parsing SRT file: {args.srt_path}")
        # Pass the file path directly to parse_srt
        parsed_subtitles = parse_srt(args.srt_path, chunk_max_blocks=config.chunk_max_blocks)
        logger.info(f"Parsed {len(parsed_subtitles)} chunks.")

        # 3. Call detect_context
        logger.info(f"Calling detect_context in '{args.speed_mode}' mode...")
        detected_context = detect_context(
            sub=parsed_subtitles,
            speed_mode=args.speed_mode,
            genai_client=genai_client,  # Pass the initialized client (or None)
            config=config
        )

        # 4. Print the result
        print(f"\nDetected Context: {detected_context}")

    except FileNotFoundError:
        logger.error(f"Error: SRT file not found at {args.srt_path}")
        print(f"Error: SRT file not found at {args.srt_path}", file=sys.stderr)
        sys.exit(1)
    except (ParsingError, ContextDetectionError, ValueError) as e:
        logger.error(f"An error occurred: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected error occurred.") # Log full traceback for unexpected errors
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
