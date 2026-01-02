"""PDF-to-Markdown Converter.

Enterprise-grade PDF-to-Markdown conversion with security sandboxing,
multi-cloud storage, RBAC, and LLM token counting.
"""

__version__ = "1.0.0"
__author__ = "PDF2MD Contributors"

from pdf2md.core.config import Settings
from pdf2md.core.converter import PDFConverter

__all__ = ["Settings", "PDFConverter", "__version__", "__author__"]
