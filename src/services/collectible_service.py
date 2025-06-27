"""Main service for collectible processing and filtering"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List

from loguru import logger

from ..models.collectible import (Collectible, CollectibleBatch,
                                  CollectibleFilter, ProcessingResult)
from ..utils.image_processor import ImageProcessor


class CollectibleService:
    """Service for processing and filtering collectibles"""

    def __init__(self, image_processor: ImageProcessor, max_workers: int = 10):
        """Initialize collectible service

        Args:
            image_processor: Image processing utility
            max_workers: Maximum number of concurrent workers
        """
        self.image_processor = image_processor
        self.max_workers = max_workers
        self._compiled_patterns = {}

    def filter_collectibles(
        self, collectibles: List[Collectible], filter_config: CollectibleFilter
    ) -> CollectibleBatch:
        """Filter collectibles based on configuration

        Args:
            collectibles: List of collectibles to filter
            filter_config: Filter configuration

        Returns:
            CollectibleBatch with filtered items
        """
        if not collectibles:
            logger.warning("No collectibles provided for filtering")
            return CollectibleBatch(total_count=0, filtered_count=0)

        collectible_count = len(collectibles)
        filter_types = filter_config.types
        logger.info(
            f"Filtering {collectible_count} items for types: {filter_types}"
        )

        # Create optimized regex pattern
        pattern = self._get_compiled_pattern(filter_config.types)

        batch = CollectibleBatch(total_count=len(collectibles))

        for collectible in collectibles:
            try:
                if self._matches_filter(collectible, pattern, filter_config):
                    batch.add_collectible(collectible)
            except Exception as e:
                logger.warning(
                    f"Error filtering collectible {collectible.id}: {e}"
                )
                continue

        logger.info(f"Found {batch.filtered_count} matching collectibles")
        return batch

    def _get_compiled_pattern(self, types: List[str]) -> re.Pattern:
        """Get or create compiled regex pattern for types

        Args:
            types: List of types to match

        Returns:
            Compiled regex pattern
        """
        types_key = tuple(sorted(types))

        if types_key not in self._compiled_patterns:
            escaped_terms = [re.escape(term) for term in types]
            pattern_str = r"(?i)\b(?:" + "|".join(escaped_terms) + r")\b"
            self._compiled_patterns[types_key] = re.compile(pattern_str)

        return self._compiled_patterns[types_key]

    def _matches_filter(
        self,
        collectible: Collectible,
        pattern: re.Pattern,
        filter_config: CollectibleFilter,
    ) -> bool:
        """Check if collectible matches filter criteria

        Args:
            collectible: Collectible to check
            pattern: Compiled regex pattern
            filter_config: Filter configuration

        Returns:
            True if collectible matches filter
        """
        # Check image requirement
        if filter_config.require_image and not collectible.image:
            return False

        # Check type field
        if collectible.type and pattern.search(collectible.type.lower()):
            return True

        # Check name and description
        name_description = (
            f"{collectible.name or ''} {collectible.description or ''}".lower()
        )
        if pattern.search(name_description):
            return True

        return False

    def process_images_concurrent(
        self, collectibles: List[Collectible], output_folder: Path
    ) -> List[ProcessingResult]:
        """Process images concurrently

        Args:
            collectibles: List of collectibles to process
            output_folder: Directory to save processed images

        Returns:
            List of processing results
        """
        if not collectibles:
            logger.warning("No collectibles to process")
            return []

        # Filter collectibles with images
        collectibles_with_images = [c for c in collectibles if c.image]
        image_count = len(collectibles_with_images)
        logger.info(
            f"Processing {image_count} images with {self.max_workers} workers"
        )

        # Ensure output folder exists
        output_folder.mkdir(parents=True, exist_ok=True)

        results = []
        successful_downloads = 0
        failed_downloads = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_collectible = {
                executor.submit(
                    self._process_single_image, collectible, output_folder
                ): collectible
                for collectible in collectibles_with_images
            }

            # Process completed downloads with progress tracking
            for future in as_completed(future_to_collectible):
                result = future.result()
                results.append(result)

                if result.success:
                    successful_downloads += 1
                    logger.debug(
                        f"Successfully processed: {result.image_name}"
                    )
                else:
                    failed_downloads += 1
                    logger.warning(f"Failed to process: {result.image_name}")

                # Log progress every 10 completions
                total_completed = successful_downloads + failed_downloads
                if total_completed % 10 == 0 or total_completed == len(
                    collectibles_with_images
                ):
                    total_images = len(collectibles_with_images)
                    logger.info(
                        f"Progress: {total_completed}/{total_images} processed"
                    )

        logger.info(
            f"Image processing complete: {successful_downloads} successful, "
            f"{failed_downloads} failed"
        )
        return results

    def _process_single_image(
        self, collectible: Collectible, output_folder: Path
    ) -> ProcessingResult:
        """Process a single collectible image

        Args:
            collectible: Collectible to process
            output_folder: Directory to save the image

        Returns:
            ProcessingResult with operation details
        """
        collectible_id = collectible.id.replace("collectible-", "")
        image_name = f"{collectible_id}.png"
        image_path = output_folder / image_name

        try:
            if not collectible.image:
                return ProcessingResult(
                    collectible_id=collectible_id,
                    image_name=image_name,
                    success=False,
                    error_message="No image URL provided",
                )

            # Use image processor to download and process
            success = self.image_processor.download_and_process_image(
                image_url=str(collectible.image), output_path=image_path
            )

            if success:
                return ProcessingResult(
                    collectible_id=collectible_id,
                    image_name=image_name,
                    success=True,
                    file_path=str(image_path),
                )
            else:
                return ProcessingResult(
                    collectible_id=collectible_id,
                    image_name=image_name,
                    success=False,
                    error_message="Image processing failed",
                )

        except Exception as e:
            logger.error(f"Error processing image for {collectible_id}: {e}")
            return ProcessingResult(
                collectible_id=collectible_id,
                image_name=image_name,
                success=False,
                error_message=str(e),
            )
