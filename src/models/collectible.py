"""Pydantic models for CS:GO collectibles"""

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class Collectible(BaseModel):
    """Pydantic model for a CS:GO collectible item"""

    id: str = Field(description="Unique collectible identifier")
    name: Optional[str] = Field(
        default=None, description="Display name of the collectible"
    )
    description: Optional[str] = Field(default=None, description="Item description")
    type: Optional[str] = Field(
        default=None, description="Collectible type (medal, coin, pin, etc.)"
    )
    image: Optional[HttpUrl] = Field(
        default=None, description="URL to the collectible image"
    )

    @validator("id")
    def validate_id(cls, v):
        """Ensure ID is not empty"""
        if not v or not v.strip():
            raise ValueError("Collectible ID cannot be empty")
        return v.strip()

    @validator("image", pre=True)
    def validate_image_url(cls, v):
        """Handle empty image URLs"""
        if v == "" or v is None:
            return None
        return v

    class Config:
        """Pydantic configuration"""

        validate_assignment = True
        use_enum_values = True


class CollectibleFilter(BaseModel):
    """Filter configuration for collectibles"""

    types: List[str] = Field(
        default_factory=lambda: [
            "pick",
            "coin",
            "medal",
            "pin",
            "trophy",
            "badge",
            "pass",
            "stars",
        ],
        description="List of collectible types to filter",
    )
    require_image: bool = Field(
        default=True, description="Only include items with image URLs"
    )

    @validator("types")
    def validate_types(cls, v):
        """Ensure types list is not empty"""
        if not v:
            raise ValueError("Filter types cannot be empty")
        return [t.lower().strip() for t in v if t.strip()]


class ProcessingResult(BaseModel):
    """Result of image processing operation"""

    collectible_id: str = Field(description="ID of the processed collectible")
    image_name: str = Field(description="Generated image filename")
    success: bool = Field(description="Whether processing was successful")
    error_message: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )
    file_path: Optional[str] = Field(
        default=None, description="Path to the saved image file"
    )

    class Config:
        """Pydantic configuration"""

        validate_assignment = True


class CollectibleBatch(BaseModel):
    """Batch of collectibles for processing"""

    items: List[Collectible] = Field(
        default_factory=list, description="List of collectibles"
    )
    total_count: int = Field(
        default=0, description="Total number of items in the batch"
    )
    filtered_count: int = Field(
        default=0, description="Number of items after filtering"
    )

    @validator("total_count", "filtered_count")
    def validate_counts(cls, v):
        """Ensure counts are non-negative"""
        if v < 0:
            raise ValueError("Counts cannot be negative")
        return v

    def add_collectible(self, collectible: Collectible) -> None:
        """Add a collectible to the batch"""
        self.items.append(collectible)
        self.filtered_count = len(self.items)

    def get_with_images(self) -> List[Collectible]:
        """Get only collectibles that have image URLs"""
        return [item for item in self.items if item.image is not None]
