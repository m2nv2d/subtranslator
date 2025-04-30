import argparse
import asyncio
from pathlib import Path
import sys
import os

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from translator import parse_srt
from translator import ValidationError, ParsingError

async def main():
    parser = argparse.ArgumentParser(description="Debug script for SRT parser.")
    parser.add_argument(
        "name",
        choices=['short', 'medium', 'long'],
        help="Name of the sample file to parse (short.srt, medium.srt, or long.srt)."
    )
    parser.add_argument(
        "--max-blocks", type=int, default=100, help="Max blocks per chunk (default: 100)."
    )
    args = parser.parse_args()

    srt_file_path = project_root / 'tests' / 'samples' / f"{args.name}.srt"
    max_blocks_per_chunk = args.max_blocks

    if not srt_file_path.exists():
        print(f"Error: Sample file not found at {srt_file_path}", file=sys.stderr)
        sys.exit(1)

    try:
        print(f"Parsing '{srt_file_path}' with max_blocks={max_blocks_per_chunk}...")
        # Call the parser function directly with the file path
        chunks = await parse_srt(str(srt_file_path), max_blocks_per_chunk)

        print(f"\nSuccessfully parsed. Number of chunks created: {len(chunks)}")

        if chunks:
            print(f"\n--- First Chunk ---")
            first_chunk = chunks[0]
            for i, block in enumerate(first_chunk): # Limit to first 5 blocks
                print(f"Block {i+1} (Original Index {block.index}):")
                print(f"  Time: {block.start} --> {block.end}")
                # Replace newlines in content for cleaner single-line preview
                content_preview = block.content.replace('\n', ' ').strip()
                print(f"  Content: '{content_preview[:80]}...'" if len(content_preview) > 80 else f"  Content: '{content_preview}'")
                print("-" * 15)
        else:
            print("\nNo subtitle blocks found or the file was empty after parsing.")

    except (ValidationError, ParsingError) as e:
        print(f"\nError during parsing: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected exceptions during the process
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc() # Print stack trace for unexpected errors
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
