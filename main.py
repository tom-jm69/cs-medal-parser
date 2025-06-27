#!/bin/env python3

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from io import BytesIO
from typing import List, Optional, Tuple

import requests
from loguru import logger
from PIL import Image
from requests.adapters import HTTPAdapter
from requests.models import HTTPError
from urllib3.util.retry import Retry

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


def create_session() -> requests.Session:
    """Creates a requests session with retry strategy and connection pooling."""
    session = requests.Session()

    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy, pool_connections=20, pool_maxsize=20
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def fetch_collectibles(url: str) -> Optional[List]:
    """Fetches latest collectibles in json format from api with improved error handling."""
    if not url:
        raise ValueError("URL not provided!")

    session = create_session()
    try:
        logger.info(f"Fetching collectibles from {url}")
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        content = response.json()
        logger.info(f"Successfully fetched {len(content)} collectibles")
        return content
    except requests.RequestException as e:
        logger.error(f"Failed to fetch collectibles: {e}")
        raise HTTPError(f"Failed to fetch collectibles: {e}")
    finally:
        session.close()


def dump_collectibles(collectibles: list) -> None:
    """Dumps all collectibles from a list to a json file with improved error handling."""
    if not collectibles:
        raise ValueError("Missing collectibles variable!")

    if not os.path.exists(DUMP_FOLDER):
        os.makedirs(DUMP_FOLDER)

    now = datetime.strftime(datetime.now(), format="%d_%m_%Y_%H_%M_%S")
    filepath = os.path.join(DUMP_FOLDER, f"collectibles_{now}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(collectibles, f, ensure_ascii=False, indent=4)
        logger.info(
            f"Successfully dumped {len(collectibles)} collectibles to {filepath}"
        )
    except IOError as e:
        logger.error(f"Failed to dump collectibles: {e}")
        raise


def filter_types(collectibles: list, filter: list[str]) -> Optional[list]:
    """Filters out specific types from collectibles with improved regex and error handling."""
    if not collectibles:
        raise ValueError("Missing collectibles variable!")

    collected = []

    # Create optimized regex pattern
    escaped_terms = [re.escape(term) for term in filter]
    filter_pattern = re.compile(r"(?i)\b(?:" + "|".join(escaped_terms) + r")\b")

    logger.info(f"Filtering {len(collectibles)} collectibles for types: {filter}")

    for count, collectible in enumerate(collectibles):
        try:
            # Validate required fields
            collectible_id = collectible.get("id")
            if not collectible_id:
                logger.warning(f"Collectible {count} missing 'id', skipping")
                continue

            collectible_type = collectible.get("type", "")
            name_description = f"{collectible.get('name', '')} {collectible.get('description', '')}".lower()

            # Check type or name/description for matches
            if (
                collectible_type and filter_pattern.search(collectible_type.lower())
            ) or filter_pattern.search(name_description):
                collected.append(
                    {"id": collectible_id, "image": collectible.get("image")}
                )
        except Exception as e:
            logger.warning(f"Error processing collectible {count}: {e}")
            continue

    logger.info(f"Found {len(collected)} matching collectibles")
    return collected if collected else None


def validate_image(img_data: bytes) -> bool:
    """Validates if the downloaded data is a valid image."""
    try:
        img = Image.open(BytesIO(img_data))
        img.verify()
        return True
    except Exception:
        return False


def resize_and_pad_image(img: Image.Image) -> Image.Image:
    """Resizes the image while maintaining aspect ratio and pads it to target dimensions."""
    # Resize while maintaining aspect ratio
    img.thumbnail((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # Calculate padding for centering
    padding_left = (TARGET_WIDTH - img.width) // 2
    padding_top = (TARGET_HEIGHT - img.height) // 2

    # Create new image with transparent background
    new_img = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    new_img.paste(img, (padding_left, padding_top))

    return new_img


def download_and_process_image(
    collectible: dict, output_folder: str, session: requests.Session
) -> Tuple[str, bool]:
    """Downloads and processes a single image with error handling."""
    collectible_id = collectible.get("id", "").strip("collectible-")
    image_name = f"{collectible_id}.png"
    image_url = collectible.get("image")
    image_path = os.path.join(output_folder, image_name)

    if not image_url:
        return image_name, False

    try:
        # Check if image already exists with correct dimensions
        if os.path.exists(image_path):
            try:
                with Image.open(image_path) as existing_img:
                    if existing_img.size == (TARGET_WIDTH, TARGET_HEIGHT):
                        return image_name, True  # Already processed correctly
                    else:
                        logger.info(f"Resizing existing image {image_name}")
            except Exception as e:
                logger.warning(
                    f"Existing image {image_name} corrupted, re-downloading: {e}"
                )

        # Download image
        response = session.get(image_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        # Validate downloaded data
        if not validate_image(response.content):
            logger.error(f"Downloaded data for {image_name} is not a valid image")
            return image_name, False

        # Process image
        img = Image.open(BytesIO(response.content))
        img = resize_and_pad_image(img)

        # Save image
        img.save(image_path, "PNG", optimize=True)
        return image_name, True

    except requests.RequestException as e:
        logger.error(f"Network error downloading {image_name}: {e}")
        return image_name, False
    except Exception as e:
        logger.error(f"Error processing image {image_name}: {e}")
        return image_name, False


def save_image(collectibles: list, output_folder: str) -> None:
    """Saves collectible images using concurrent downloads for improved performance."""
    if not collectibles:
        logger.warning("No collectibles to process")
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    logger.info(f"Processing {len(collectibles)} images with {MAX_WORKERS} workers")

    session = create_session()
    successful_downloads = 0
    failed_downloads = 0

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all download tasks
            future_to_collectible = {
                executor.submit(
                    download_and_process_image, collectible, output_folder, session
                ): collectible
                for collectible in collectibles
            }

            # Process completed downloads with progress tracking
            for future in as_completed(future_to_collectible):
                image_name, success = future.result()
                if success:
                    successful_downloads += 1
                    logger.debug(f"Successfully processed: {image_name}")
                else:
                    failed_downloads += 1
                    logger.warning(f"Failed to process: {image_name}")

                # Log progress every 10 completions
                total_completed = successful_downloads + failed_downloads
                if total_completed % 10 == 0 or total_completed == len(collectibles):
                    logger.info(
                        f"Progress: {total_completed}/{len(collectibles)} images processed"
                    )

    finally:
        session.close()

    logger.info(
        f"Image processing complete: {successful_downloads} successful, {failed_downloads} failed"
    )


def main() -> None:
    """Main function with improved error handling and logging."""
    start_time = time.time()
    logger.info("Starting CS:GO Medal Parser")

    try:
        # Fetch collectibles
        collectibles = fetch_collectibles(COLLECTIBLES_URL)
        if not collectibles:
            logger.error("No collectibles fetched")
            return

        # Dump collectibles
        dump_collectibles(collectibles)

        # Filter collectibles
        filtered_collectibles = filter_types(collectibles, COLLECTIBLE_TYPES)
        if not filtered_collectibles:
            logger.warning("No collectibles matched the filter criteria")
            return

        # Save images
        save_image(filtered_collectibles, OUTPUT_FOLDER)

        elapsed_time = time.time() - start_time
        logger.success(
            f"Medal parser completed successfully in {elapsed_time:.2f} seconds"
        )

    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}")
        raise


if __name__ == "__main__":
    main()
