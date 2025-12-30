"""PDF extraction engines with automatic fallback."""

from pdf2md.extractors.base import (
    PDFExtraction,
    PDFExtractionError,
    PDFExtractor,
    PDFMetadata,
    PDFPage,
)
from pdf2md.extractors.factory import AutoFallbackExtractor, ExtractorFactory
from pdf2md.extractors.pdfplumber_extractor import PDFPlumberExtractor
from pdf2md.extractors.pymupdf_extractor import PyMuPDFExtractor

__all__ = [
    "PDFExtractor",
    "PDFExtraction",
    "PDFMetadata",
    "PDFPage",
    "PDFExtractionError",
    "PDFPlumberExtractor",
    "PyMuPDFExtractor",
    "AutoFallbackExtractor",
    "ExtractorFactory",
]