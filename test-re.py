import json
import os
from pathlib import Path

from loguru import logger

from config import COLLECTIBLE_TYPES, DUMP_FOLDER
from main import filter_types


def find_newest_json_file(directory: str) -> str | None:
    """Finds the newest JSON file in the specified directory."""
    if not os.path.exists(directory):
        logger.error(f"Directory {directory} does not exist")
        return None

    newest_file = None
    newest_creation_time = 0

    try:
        for file in os.listdir(directory):
            if file.endswith(".json"):
                file_path = os.path.join(directory, file)
                creation_time = os.path.getctime(file_path)

                if creation_time > newest_creation_time:
                    newest_file = file
                    newest_creation_time = creation_time

        return newest_file
    except OSError as e:
        logger.error(f"Error reading directory {directory}: {e}")
        return None


def main():
    """Main function for testing the regex filtering."""
    logger.info("Starting regex filter test")

    newest_file = find_newest_json_file(DUMP_FOLDER)

    if not newest_file:
        logger.error("No JSON files found in dump folder")
        return

    logger.info(f"Using newest file: {newest_file}")

    try:
        file_path = os.path.join(DUMP_FOLDER, newest_file)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data)} collectibles from {newest_file}")

        # Test the filtering function
        filtered = filter_types(data, COLLECTIBLE_TYPES)

        if filtered:
            logger.info(f"Filter test successful: {len(filtered)} collectibles matched")

            # Save filtered results
            output_file = "filtered.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered, f, ensure_ascii=False, indent=4)

            logger.success(f"Filtered results saved to {output_file}")

            # Show sample results
            sample_size = min(5, len(filtered))
            logger.info(f"Sample of first {sample_size} filtered results:")
            for i, item in enumerate(filtered[:sample_size]):
                logger.info(
                    f"  {i+1}. ID: {item.get('id')}, Image: {item.get('image', 'N/A')[:50]}..."
                )
        else:
            logger.warning("No collectibles matched the filter criteria")

    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {newest_file}: {e}")
    except IOError as e:
        logger.error(f"Error reading file {newest_file}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
