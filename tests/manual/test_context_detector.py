import argparse
import logging
import sys
from pathlib import Path

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from config_loader import load_config
from translator import init_genai_client, parse_srt, detect_context
from translator import ContextDetectionError, ParsingError

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Debug script for context_detector.")
    parser.add_argument(
        "name",
        choices=['short', 'medium', 'long'],
        help="Name of the sample file to parse (short.srt, medium.srt, or long.srt)."
    )
    parser.add_argument(
        "--speed-mode",
        type=str,
        default="fast",
        choices=["mock", "fast", "normal"],
        help="Translation mode ('mock', 'fast', or 'normal')."
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )
    args = parser.parse_args()

    # Setup logging with user-specified level
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    srt_file_path = project_root / 'tests' / 'samples' / f"{args.name}.srt"
    logger.info(f"Starting debug script for {srt_file_path} with mode '{args.speed_mode}'...")

    try:
        # 1. Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Initialize GenAI client only if needed
        genai_client = None
        if args.speed_mode != "mock":
            logger.info("Initializing GenAI client...")
            try:
                genai_client = init_genai_client(config)
                logger.info("GenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}. Proceeding without client for context detection.")

        # === Check if SRT file exists ===
        if not srt_file_path.exists():
            logger.error(f"Error: Sample file not found at {srt_file_path}")
            sys.exit(1)

        # 2. Parse the SRT file
        logger.info(f"Parsing SRT file: {srt_file_path}")
        # Pass the file path directly to parse_srt
        parsed_subtitles = parse_srt(str(srt_file_path), chunk_max_blocks=config.chunk_max_blocks)
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
        logger.error(f"Error: Sample file not found at {srt_file_path}")
        print(f"Error: Sample file not found at {srt_file_path}", file=sys.stderr)
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
