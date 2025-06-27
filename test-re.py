#!/usr/bin/env python3
"""
Test script for CS:GO Medal Parser regex filtering functionality
"""

import json
import sys
from pathlib import Path

from loguru import logger

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import COLLECTIBLE_TYPES, DUMP_FOLDER
from src.models.collectible import Collectible, CollectibleFilter
from src.services.collectible_service import CollectibleService
from src.utils.image_processor import ImageProcessor


def find_newest_json_file(directory: Path) -> Path | None:
    """Finds the newest JSON file in the specified directory.

    Args:
        directory: Directory to search in

    Returns:
        Path to newest JSON file or None if not found
    """
    if not directory.exists():
        logger.error(f"Directory {directory} does not exist")
        return None

    try:
        json_files = list(directory.glob("*.json"))
        if not json_files:
            return None

        # Find the newest file by creation time
        newest_file = max(json_files, key=lambda f: f.stat().st_ctime)
        return newest_file

    except Exception as e:
        logger.error(f"Error reading directory {directory}: {e}")
        return None


def load_collectibles_from_file(file_path: Path) -> list[Collectible]:
    """Load collectibles from JSON file and convert to Pydantic models

    Args:
        file_path: Path to the JSON file

    Returns:
        List of Collectible objects
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        collectibles = []
        for item_data in raw_data:
            try:
                collectible = Collectible(**item_data)
                collectibles.append(collectible)
            except Exception as e:
                logger.warning(
                    f"Failed to parse collectible {item_data.get('id', 'unknown')}: {e}"
                )
                continue

        return collectibles

    except Exception as e:
        logger.error(f"Error loading collectibles from {file_path}: {e}")
        return []


def save_filtered_results(collectibles: list[Collectible], output_file: str) -> bool:
    """Save filtered collectibles to JSON file

    Args:
        collectibles: List of collectibles to save
        output_file: Output file path

    Returns:
        True if successful, False otherwise
    """
    try:
        # Convert back to simple dict format for compatibility
        data = [
            {"id": c.id, "image": str(c.image) if c.image else None}
            for c in collectibles
        ]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return True

    except Exception as e:
        logger.error(f"Error saving filtered results: {e}")
        return False


def main():
    """Main function for testing the regex filtering."""
    logger.info("Starting CS:GO Medal Parser - Regex Filter Test")

    dump_folder = Path(DUMP_FOLDER)
    newest_file = find_newest_json_file(dump_folder)

    if not newest_file:
        logger.error(f"No JSON files found in {dump_folder}")
        return

    logger.info(f"Using newest file: {newest_file.name}")

    # Load collectibles
    collectibles = load_collectibles_from_file(newest_file)
    if not collectibles:
        logger.error("Failed to load collectibles from file")
        return

    logger.info(f"Loaded {len(collectibles)} collectibles from {newest_file.name}")

    # Initialize services for testing
    image_processor = ImageProcessor()
    collectible_service = CollectibleService(image_processor)
    filter_config = CollectibleFilter(types=COLLECTIBLE_TYPES)

    # Test the filtering function
    filtered_batch = collectible_service.filter_collectibles(
        collectibles, filter_config
    )

    if filtered_batch.items:
        logger.info(
            f"Filter test successful: {filtered_batch.filtered_count} collectibles matched"
        )

        # Save filtered results
        output_file = "filtered.json"
        if save_filtered_results(filtered_batch.items, output_file):
            logger.success(f"Filtered results saved to {output_file}")

        # Show sample results
        sample_size = min(5, len(filtered_batch.items))
        logger.info(f"Sample of first {sample_size} filtered results:")
        for i, item in enumerate(filtered_batch.items[:sample_size]):
            image_preview = str(item.image)[:50] + "..." if item.image else "N/A"
            logger.info(f"  {i+1}. ID: {item.id}, Image: {image_preview}")

        # Show statistics
        with_images = len([c for c in filtered_batch.items if c.image])
        logger.info(f"Statistics:")
        logger.info(f"  • Total collectibles: {filtered_batch.total_count}")
        logger.info(f"  • Matched filter: {filtered_batch.filtered_count}")
        logger.info(f"  • With images: {with_images}")

    else:
        logger.warning("No collectibles matched the filter criteria")


if __name__ == "__main__":
    main()
