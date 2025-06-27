"""Main CS Medal Parser application class"""

import time
from pathlib import Path
from typing import List, Optional

from loguru import logger

from ..models.collectible import (
    Collectible,
    CollectibleBatch,
    CollectibleFilter,
    ProcessingResult,
)
from ..services.api_service import ApiService
from ..services.collectible_service import CollectibleService
from ..utils.image_processor import ImageProcessor
from ..utils.network import NetworkClient


class CSMedalParser:
    """Main application class for CS Medal Parser"""

    def __init__(
        self,
        api_url: str,
        output_folder: str,
        dump_folder: str,
        collectible_types: List[str],
        max_workers: int = 10,
        request_timeout: int = 30,
        max_retries: int = 3,
        target_width: int = 256,
        target_height: int = 192,
    ):
        """Initialize CS Medal Parser

        Args:
            api_url: URL of the collectibles API
            output_folder: Directory for processed images
            dump_folder: Directory for API response dumps
            collectible_types: List of collectible types to filter
            max_workers: Number of concurrent workers
            request_timeout: Network request timeout
            max_retries: Maximum retry attempts
            target_width: Target image width
            target_height: Target image height
        """
        self.api_url = api_url
        self.output_folder = Path(output_folder)
        self.dump_folder = Path(dump_folder)

        # Initialize configuration
        self.filter_config = CollectibleFilter(types=collectible_types)

        # Initialize services
        self.network_client = NetworkClient(
            timeout=request_timeout, max_retries=max_retries
        )
        self.image_processor = ImageProcessor(
            target_width=target_width,
            target_height=target_height,
            network_client=self.network_client,
        )

        self.api_service = ApiService(
            base_url=api_url, timeout=request_timeout, max_retries=max_retries
        )

        self.collectible_service = CollectibleService(
            image_processor=self.image_processor, max_workers=max_workers
        )

    def run(self) -> bool:
        """Run the complete medal parsing process

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        logger.info("Starting CS:GO Medal Parser")

        try:
            # Step 1: Fetch collectibles from API
            collectibles = self._fetch_collectibles()
            if not collectibles:
                logger.error("No collectibles fetched from API")
                return False

            # Step 2: Dump raw data
            self._dump_collectibles(collectibles)

            # Step 3: Filter collectibles
            filtered_batch = self._filter_collectibles(collectibles)
            if not filtered_batch.items:
                logger.warning("No collectibles matched the filter criteria")
                return False

            # Step 4: Process images
            results = self._process_images(filtered_batch.items)

            # Step 5: Log final results
            self._log_final_results(results, start_time)

            return True

        except Exception as e:
            logger.error(f"Fatal error in main execution: {e}")
            return False

    def _fetch_collectibles(self) -> Optional[List[Collectible]]:
        """Fetch collectibles from API

        Returns:
            List of collectibles or None if failed
        """
        try:
            return self.api_service.fetch_collectibles_sync()
        except Exception as e:
            logger.error(f"Failed to fetch collectibles: {e}")
            return None

    def _dump_collectibles(self, collectibles: List[Collectible]) -> Optional[Path]:
        """Dump collectibles to JSON file

        Args:
            collectibles: List of collectibles to dump

        Returns:
            Path to dump file or None if failed
        """
        try:
            return self.api_service.dump_collectibles(collectibles, self.dump_folder)
        except Exception as e:
            logger.error(f"Failed to dump collectibles: {e}")
            return None

    def _filter_collectibles(self, collectibles: List[Collectible]) -> CollectibleBatch:
        """Filter collectibles based on configuration

        Args:
            collectibles: List of collectibles to filter

        Returns:
            Filtered collectible batch
        """
        return self.collectible_service.filter_collectibles(
            collectibles, self.filter_config
        )

    def _process_images(
        self, collectibles: List[Collectible]
    ) -> List[ProcessingResult]:
        """Process collectible images

        Args:
            collectibles: List of collectibles to process

        Returns:
            List of processing results
        """
        return self.collectible_service.process_images_concurrent(
            collectibles, self.output_folder
        )

    def _log_final_results(
        self, results: List[ProcessingResult], start_time: float
    ) -> None:
        """Log final processing results

        Args:
            results: List of processing results
            start_time: Start time for performance calculation
        """
        elapsed_time = time.time() - start_time
        successful_count = sum(1 for r in results if r.success)
        failed_count = len(results) - successful_count

        logger.info("Processing Summary:")
        logger.info(f"  • Total images processed: {len(results)}")
        logger.info(f"  • Successful: {successful_count}")
        logger.info(f"  • Failed: {failed_count}")
        logger.info(f"  • Execution time: {elapsed_time:.2f} seconds")

        if failed_count > 0:
            logger.warning(f"Failed to process {failed_count} images")
            # Log a few failed items for debugging
            failed_results = [r for r in results if not r.success][:5]
            for result in failed_results:
                logger.debug(f"Failed: {result.image_name} - {result.error_message}")

        logger.success(f"CS:GO Medal Parser completed in {elapsed_time:.2f} seconds")

    def get_stats(self) -> dict:
        """Get current statistics

        Returns:
            Dictionary with current statistics
        """
        output_images = (
            list(self.output_folder.glob("*.png"))
            if self.output_folder.exists()
            else []
        )
        dump_files = (
            list(self.dump_folder.glob("*.json")) if self.dump_folder.exists() else []
        )

        return {
            "output_images_count": len(output_images),
            "dump_files_count": len(dump_files),
            "output_folder": str(self.output_folder),
            "dump_folder": str(self.dump_folder),
            "filter_types": self.filter_config.types,
        }
