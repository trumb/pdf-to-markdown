"""PyMuPDF-based PDF extractor (fallback engine)."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from pdf2md.extractors.base import (
    PDFExtraction,
    PDFExtractor,
    PDFExtractionError,
    PDFMetadata,
    PDFPage,
)


class PyMuPDFExtractor(PDFExtractor):
    """PDF extractor using PyMuPDF library (fallback engine)."""

    @property
    def name(self) -> str:
        """Return extractor name."""
        return "pymupdf"

    def validate_pdf(self, pdf_path: Path) -> bool:
        """Validate that file is a readable PDF."""
        if not pdf_path.exists():
            return False

        if not pdf_path.is_file():
            return False

        # Check magic bytes
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    return False
        except Exception:
            return False

        # Attempt to open with PyMuPDF
        try:
            doc = fitz.open(pdf_path)
            doc.close()
            return True
        except Exception:
            return False

    def get_metadata(self, pdf_path: Path) -> PDFMetadata:
        """Extract metadata from PDF."""
        if not self.validate_pdf(pdf_path):
            raise PDFExtractionError(f"Invalid PDF file: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            metadata_dict = doc.metadata

            # Parse dates
            creation_date = self._parse_pdf_date(metadata_dict.get("creationDate"))
            mod_date = self._parse_pdf_date(metadata_dict.get("modDate"))

            result = PDFMetadata(
                title=metadata_dict.get("title") or None,
                author=metadata_dict.get("author") or None,
                subject=metadata_dict.get("subject") or None,
                creator=metadata_dict.get("creator") or None,
                producer=metadata_dict.get("producer") or None,
                creation_date=creation_date,
                modification_date=mod_date,
                page_count=doc.page_count,
                encrypted=doc.is_encrypted,
                file_size_bytes=pdf_path.stat().st_size,
            )

            doc.close()
            return result

        except Exception as e:
            raise PDFExtractionError(f"Failed to extract metadata: {e}") from e

    def extract(self, pdf_path: Path) -> PDFExtraction:
        """Extract full content from PDF."""
        start_time = time.time()
        warnings: list[str] = []

        if not self.validate_pdf(pdf_path):
            raise PDFExtractionError(f"Invalid PDF file: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)

            # Extract metadata
            metadata = self.get_metadata(pdf_path)

            # Extract pages
            pages: list[PDFPage] = []
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_data = self._extract_page(page, page_num + 1)
                    pages.append(page_data)
                except Exception as e:
                    warnings.append(f"Page {page_num + 1} extraction failed: {e}")
                    # Create empty page on failure
                    pages.append(
                        PDFPage(
                            page_number=page_num + 1,
                            text="",
                            images=[],
                            tables=[],
                            width=0.0,
                            height=0.0,
                        )
                    )

            doc.close()

            extraction_time = time.time() - start_time

            return PDFExtraction(
                metadata=metadata,
                pages=pages,
                extraction_method=self.name,
                extraction_time_seconds=extraction_time,
                warnings=warnings,
            )

        except Exception as e:
            raise PDFExtractionError(f"PDF extraction failed: {e}") from e

    def _extract_page(self, page: Any, page_num: int) -> PDFPage:
        """Extract content from a single page."""
        # Extract text
        text = page.get_text()

        # Extract image information
        images: list[dict[str, Any]] = []
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            bbox = page.get_image_bbox(xref)
            if bbox:
                images.append(
                    {
                        "x0": bbox.x0,
                        "y0": bbox.y0,
                        "x1": bbox.x1,
                        "y1": bbox.y1,
                        "width": bbox.width,
                        "height": bbox.height,
                    }
                )

        # PyMuPDF doesn't have built-in table extraction
        # This is a known limitation compared to pdfplumber
        tables: list[dict[str, Any]] = []

        rect = page.rect
        return PDFPage(
            page_number=page_num,
            text=text,
            images=images,
            tables=tables,
            width=rect.width,
            height=rect.height,
        )

    def _parse_pdf_date(self, date_str: str | None) -> datetime | None:
        """Parse PDF date string to datetime."""
        if not date_str:
            return None

        # PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm
        try:
            # Remove D: prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]

            # Extract basic components
            if len(date_str) >= 14:
                year = int(date_str[0:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                hour = int(date_str[8:10])
                minute = int(date_str[10:12])
                second = int(date_str[12:14])

                return datetime(year, month, day, hour, minute, second)
        except Exception:
            pass

        return None
