#!/usr/bin/env python3
"""
CS:GO Medal Parser - Professional Implementation

A high-performance application for parsing and downloading CS:GO collectibles
with concurrent processing, advanced error handling, and structured logging.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import (
    COLLECTIBLE_TYPES,
    COLLECTIBLES_URL,
    DUMP_FOLDER,
    MAX_RETRIES,
    MAX_WORKERS,
    OUTPUT_FOLDER,
    REQUEST_TIMEOUT,
    TARGET_HEIGHT,
    TARGET_WIDTH,
)
from src.core.parser import CSMedalParser


def main() -> int:
    """Main entry point for the CS:GO Medal Parser application

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    try:
        # Initialize the parser with configuration
        parser = CSMedalParser(
            api_url=COLLECTIBLES_URL,
            output_folder=OUTPUT_FOLDER,
            dump_folder=DUMP_FOLDER,
            collectible_types=COLLECTIBLE_TYPES,
            max_workers=MAX_WORKERS,
            request_timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
            target_width=TARGET_WIDTH,
            target_height=TARGET_HEIGHT,
        )

        # Run the parser
        success = parser.run()

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
