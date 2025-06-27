"""Image processing utilities"""

from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger
from PIL import Image

from .network import NetworkClient


class ImageProcessor:
    """Utility class for image processing operations"""

    def __init__(
        self,
        target_width: int = 256,
        target_height: int = 192,
        network_client: Optional[NetworkClient] = None,
    ):
        """Initialize image processor

        Args:
            target_width: Target image width in pixels
            target_height: Target image height in pixels
            network_client: Optional network client for downloads
        """
        self.target_width = target_width
        self.target_height = target_height
        self.network_client = network_client or NetworkClient()

    def validate_image_data(self, img_data: bytes) -> bool:
        """Validate if the downloaded data is a valid image

        Args:
            img_data: Raw image data bytes

        Returns:
            True if data is a valid image
        """
        try:
            img = Image.open(BytesIO(img_data))
            img.verify()
            return True
        except Exception:
            return False

    def resize_and_pad_image(self, img: Image.Image) -> Image.Image:
        """Resize image while maintaining aspect ratio and pad to target dimensions

        Args:
            img: PIL Image object

        Returns:
            Processed PIL Image object
        """
        # Create a copy to avoid modifying the original
        img = img.copy()

        # Resize while maintaining aspect ratio
        img.thumbnail((self.target_width, self.target_height), Image.Resampling.LANCZOS)

        # Calculate padding for centering
        padding_left = (self.target_width - img.width) // 2
        padding_top = (self.target_height - img.height) // 2

        # Create new image with transparent background
        new_img = Image.new(
            "RGBA", (self.target_width, self.target_height), (0, 0, 0, 0)
        )
        new_img.paste(img, (padding_left, padding_top))

        return new_img

    def process_image_from_bytes(self, img_data: bytes) -> Optional[Image.Image]:
        """Process image from raw bytes

        Args:
            img_data: Raw image data

        Returns:
            Processed PIL Image object or None if failed
        """
        try:
            # Validate image data
            if not self.validate_image_data(img_data):
                logger.error("Invalid image data provided")
                return None

            # Open and process image
            img = Image.open(BytesIO(img_data))
            processed_img = self.resize_and_pad_image(img)

            return processed_img

        except Exception as e:
            logger.error(f"Error processing image from bytes: {e}")
            return None

    def download_and_process_image(self, image_url: str, output_path: Path) -> bool:
        """Download and process image from URL

        Args:
            image_url: URL of the image to download
            output_path: Path where to save the processed image

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if image already exists with correct dimensions
            if output_path.exists():
                try:
                    with Image.open(output_path) as existing_img:
                        if existing_img.size == (self.target_width, self.target_height):
                            return True  # Already processed correctly
                        else:
                            logger.info(f"Resizing existing image {output_path.name}")
                except Exception as e:
                    logger.warning(
                        f"Existing image {output_path.name} corrupted, re-downloading: {e}"
                    )

            # Download image data
            session = self.network_client.create_session()
            img_data = self.network_client.download_with_retry(image_url, session)
            session.close()

            if not img_data:
                logger.error(f"Failed to download image from {image_url}")
                return False

            # Process image
            processed_img = self.process_image_from_bytes(img_data)
            if not processed_img:
                logger.error(f"Failed to process image from {image_url}")
                return False

            # Save processed image
            processed_img.save(output_path, "PNG", optimize=True)
            logger.debug(f"Successfully saved image: {output_path}")

            return True

        except Exception as e:
            logger.error(
                f"Error downloading and processing image from {image_url}: {e}"
            )
            return False

    def get_image_dimensions(self, image_path: Path) -> Optional[Tuple[int, int]]:
        """Get dimensions of an image file

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (width, height) or None if failed
        """
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception as e:
            logger.error(f"Error getting dimensions for {image_path}: {e}")
            return None
