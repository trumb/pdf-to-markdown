"""PDFPlumber-based PDF extractor (primary engine)."""

import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber

from pdf2md.extractors.base import (
    PDFExtraction,
    PDFExtractor,
    PDFExtractionError,
    PDFMetadata,
    PDFPage,
)


class PDFPlumberExtractor(PDFExtractor):
    """PDF extractor using pdfplumber library (accuracy-focused)."""

    @property
    def name(self) -> str:
        """Return extractor name."""
        return "pdfplumber"

    def validate_pdf(self, pdf_path: Path) -> bool:
        """Validate that file is a readable PDF."""
        if not pdf_path.exists():
            return False

        if not pdf_path.is_file():
            return False

        # Check magic bytes for PDF signature
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(b"%PDF-"):
                    return False
        except Exception:
            return False

        # Attempt to open with pdfplumber
        try:
            with pdfplumber.open(pdf_path):
                return True
        except Exception:
            return False

    def get_metadata(self, pdf_path: Path) -> PDFMetadata:
        """Extract metadata from PDF."""
        if not self.validate_pdf(pdf_path):
            raise PDFExtractionError(f"Invalid PDF file: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                metadata_dict = pdf.metadata or {}

                # Parse dates
                creation_date = self._parse_pdf_date(
                    metadata_dict.get("CreationDate") or metadata_dict.get("CreationDate")
                )
                mod_date = self._parse_pdf_date(
                    metadata_dict.get("ModDate") or metadata_dict.get("ModificationDate")
                )

                return PDFMetadata(
                    title=metadata_dict.get("Title"),
                    author=metadata_dict.get("Author"),
                    subject=metadata_dict.get("Subject"),
                    creator=metadata_dict.get("Creator"),
                    producer=metadata_dict.get("Producer"),
                    creation_date=creation_date,
                    modification_date=mod_date,
                    page_count=len(pdf.pages),
                    encrypted=pdf.is_encrypted,
                    file_size_bytes=pdf_path.stat().st_size,
                )
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract metadata: {e}") from e

    def extract(self, pdf_path: Path) -> PDFExtraction:
        """Extract full content from PDF."""
        start_time = time.time()
        warnings: list[str] = []

        if not self.validate_pdf(pdf_path):
            raise PDFExtractionError(f"Invalid PDF file: {pdf_path}")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Extract metadata
                metadata = self.get_metadata(pdf_path)

                # Extract pages
                pages: list[PDFPage] = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        page_data = self._extract_page(page, page_num)
                        pages.append(page_data)
                    except Exception as e:
                        warnings.append(f"Page {page_num} extraction failed: {e}")
                        # Create empty page on failure
                        pages.append(
                            PDFPage(
                                page_number=page_num,
                                text="",
                                images=[],
                                tables=[],
                                width=page.width if hasattr(page, "width") else 0.0,
                                height=page.height if hasattr(page, "height") else 0.0,
                            )
                        )

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
        text = page.extract_text() or ""

        # Extract images
        images: list[dict[str, Any]] = []
        if hasattr(page, "images"):
            for img in page.images:
                images.append(
                    {
                        "x0": img.get("x0", 0),
                        "y0": img.get("y0", 0),
                        "x1": img.get("x1", 0),
                        "y1": img.get("y1", 0),
                        "width": img.get("width", 0),
                        "height": img.get("height", 0),
                    }
                )

        # Extract tables
        tables: list[dict[str, Any]] = []
        try:
            extracted_tables = page.extract_tables()
            if extracted_tables:
                for table_data in extracted_tables:
                    if table_data:
                        tables.append({"data": table_data})
        except Exception:
            # Table extraction can fail even when page extraction succeeds
            pass

        return PDFPage(
            page_number=page_num,
            text=text,
            images=images,
            tables=tables,
            width=page.width,
            height=page.height,
        )

    def _parse_pdf_date(self, date_str: str | None) -> datetime | None:
        """Parse PDF date string to datetime."""
        if not date_str:
            return None

        # PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm
        # Example: D:20231225120000Z
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