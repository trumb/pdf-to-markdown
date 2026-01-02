"""Image handling strategies for PDF conversion."""

import base64
from pathlib import Path
from typing import Any, Literal


class ImageHandler:
    """Handle images extracted from PDF with different strategies."""

    def __init__(
        self, mode: Literal["skip", "extract", "base64", "reference"] = "skip"
    ) -> None:
        """
        Initialize image handler.

        Args:
            mode: Image handling mode
                - skip: Ignore images completely
                - extract: Extract images to separate files
                - base64: Embed images as base64 data URLs
                - reference: Include image references/placeholders
        """
        self.mode = mode

    def process_images(
        self, images: list[dict[str, Any]], page_num: int, output_dir: Path | None = None
    ) -> str:
        """
        Process images from a page.

        Args:
            images: List of image dictionaries from extractor
            page_num: Page number
            output_dir: Output directory for extracted images (required for 'extract' mode)

        Returns:
            Markdown string with image references or empty string
        """
        if self.mode == "skip":
            return ""

        elif self.mode == "reference":
            # Add image placeholders
            if not images:
                return ""

            lines = []
            for idx, img in enumerate(images, start=1):
                lines.append(f"![Image {idx} on page {page_num}]()")
            return "\n".join(lines)

        elif self.mode == "base64":
            # Note: This mode requires actual image data, not just coordinates
            # In Phase 1, we only have image metadata, not pixel data
            # Full implementation deferred to Phase 2 when we can extract pixels
            return self._add_image_references(images, page_num)

        elif self.mode == "extract":
            # Extract images to files
            if not output_dir:
                raise ValueError("output_dir required for 'extract' mode")

            if not images:
                return ""

            lines = []
            for idx, img in enumerate(images, start=1):
                filename = f"page{page_num}_image{idx}.png"
                # Note: Actual pixel extraction deferred to Phase 2
                # For now, just create references
                lines.append(f"![Image {idx}]({filename})")
            return "\n".join(lines)

        return ""

    def _add_image_references(self, images: list[dict[str, Any]], page_num: int) -> str:
        """Add image reference placeholders."""
        if not images:
            return ""

        lines = []
        for idx, img in enumerate(images, start=1):
            width = img.get("width", 0)
            height = img.get("height", 0)
            lines.append(
                f"[Image {idx}: {width:.0f}x{height:.0f}px on page {page_num}]"
            )
        return "\n".join(lines)
