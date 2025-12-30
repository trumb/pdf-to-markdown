"""PDF file validation and security checks."""

import hashlib
from pathlib import Path


class PDFValidator:
    """Validates PDF files for security concerns."""

    # PDF magic bytes
    PDF_SIGNATURE = b"%PDF-"

    # Maximum file size (100 MB by default)
    MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024

    @staticmethod
    def validate_file(pdf_path: Path, max_size_mb: int = 100) -> tuple[bool, str]:
        """
        Validate PDF file for security.

        Args:
            pdf_path: Path to PDF file
            max_size_mb: Maximum allowed file size in MB

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        # Check file exists
        if not pdf_path.exists():
            return False, f"File does not exist: {pdf_path}"

        # Check is file (not directory)
        if not pdf_path.is_file():
            return False, f"Path is not a file: {pdf_path}"

        # Check file size
        file_size = pdf_path.stat().st_size
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size == 0:
            return False, "File is empty"

        if file_size > max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large: {size_mb:.1f} MB (max: {max_size_mb} MB)"

        # Check PDF magic bytes
        try:
            with open(pdf_path, "rb") as f:
                header = f.read(5)
                if not header.startswith(PDFValidator.PDF_SIGNATURE):
                    return False, "File is not a valid PDF (invalid signature)"
        except Exception as e:
            return False, f"Failed to read file: {e}"

        return True, ""

    @staticmethod
    def compute_file_hash(pdf_path: Path, algorithm: str = "sha256") -> str:
        """
        Compute hash of PDF file.

        Args:
            pdf_path: Path to PDF file
            algorithm: Hash algorithm (sha256, md5, sha1)

        Returns:
            Hex digest of file hash

        Raises:
            ValueError: If algorithm is unsupported
        """
        if algorithm not in ("sha256", "md5", "sha1"):
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        hash_func = hashlib.new(algorithm)

        with open(pdf_path, "rb") as f:
            # Read in chunks to handle large files
            while chunk := f.read(8192):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    @staticmethod
    def get_file_info(pdf_path: Path) -> dict[str, any]:  # type: ignore[misc]
        """
        Get file information for validation.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with file information
        """
        stat = pdf_path.stat()

        return {
            "path": str(pdf_path),
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "modified_timestamp": stat.st_mtime,
            "is_readable": os.access(pdf_path, os.R_OK),
            "sha256": PDFValidator.compute_file_hash(pdf_path, "sha256"),
        }


# Ensure os is imported
import os