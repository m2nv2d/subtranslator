import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from config_loader import load_config
from translator import init_genai_client, parse_srt, translate_all_chunks, detect_context, reassemble_srt
from translator import ChunkTranslationError

async def main():
    parser = argparse.ArgumentParser(description="Manual test script for reassembly flow.")
    parser.add_argument(
        "srt_file",
        type=str,
        help="Path to the input SRT file."
    )
    parser.add_argument(
        "--speed-mode",
        type=str,
        default="mock",
        choices=["mock", "fast", "normal"],
        help="Translation mode ('mock', 'fast', or 'normal')."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)."
    )

    args = parser.parse_args()

    logging.basicConfig(level=args.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"Running test with srt_file: {args.srt_file}, speed_mode: {args.speed_mode}")

    # --- Load Configuration ---
    try:
        config = load_config()
        target_lang = config.target_languages[0]
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return

    # --- Initialize GenAI Client ---
    genai_client = None
    if args.speed_mode != "mock":
        try:
            # Ensure API key is handled (e.g., via environment variables)
            genai_client = init_genai_client(config=config)
            logging.info("Gemini client initialized.")
        except Exception as e:
            logging.error(f"Error initializing Gemini client: {e}. Cannot run 'real' mode.")
            return

    # --- Parse SRT File ---
    try:
        subtitle_chunks = parse_srt(args.srt_file, config.chunk_max_blocks)
        logging.info(f"Parsed {len(subtitle_chunks)} chunks from the file.")
        if not subtitle_chunks:
            logging.error("No subtitle chunks found in the file.")
            return
    except FileNotFoundError:
        logging.error(f"SRT file not found: {args.srt_file}")
        return
    except Exception as e:
        logging.error(f"Error parsing SRT file: {e}")
        return

    # --- Detect Context ---
    try:
        logging.info("Detecting context...")
        detected_context = detect_context(
            sub=subtitle_chunks,
            speed_mode=args.speed_mode,
            genai_client=genai_client if args.speed_mode != "mock" else None,
            config=config
        )
        if detected_context:
            logging.info(f"Detected Context: {detected_context}")
            context = detected_context
        else:
            logging.warning("Could not detect context automatically. Using default prompts.")
            # Fallback to default context if detection fails
            context = f"Translate the following subtitles into {target_lang}. Maintain the timing and context."

    except Exception as e:
        logging.error(f"Error during context detection: {e}")


    # --- Run the translator ---
    logging.info(f"Starting chunk translation for {target_lang}...")
    try:
        await translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=args.speed_mode,
            genai_client=genai_client if args.speed_mode != "mock" else None,
            config=config
        )
        logging.info("Chunk translation completed.")

    except ChunkTranslationError as e:
        logging.error(f"\n--- Chunk Translation Failed --- Error: {e}")
    except Exception as e:
        logging.exception(f"\n--- An unexpected error occurred during translation --- Error: {e}") # Use logging.exception for traceback

    # --- Run the reassembly ---
    logging.info(f"Starting reassembly...")
    try:
        reassembled_content = reassemble_srt(subtitle_chunks)
        logging.info("\nReassembly completed.")

        # Save the reassembled content to the new SRT file
        input_path = Path(args.srt_file)
        output_filename = f"{input_path.stem}_translated.srt"
        output_path = input_path.parent / output_filename
        try:
            with open(output_path, 'wb') as f:
                f.write(reassembled_content)
            logging.info(f"Reassembled content saved to: {output_path}")
        except IOError as e:
            logging.error(f"Error writing reassembled content to file {output_path}: {e}")
    except Exception as e:
        logging.error(f"\n--- Reassembly Failed --- Error: {e}")

if __name__ == "__main__":    
    asyncio.run(main())