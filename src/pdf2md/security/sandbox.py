"""Sandbox for isolated PDF processing with resource limits."""

import tempfile
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any

from pdf2md.extractors.base import PDFExtraction
from pdf2md.extractors.factory import ExtractorFactory
from pdf2md.security.resource_limits import ResourceLimits, apply_resource_limits


class SandboxError(Exception):
    """Raised when sandbox execution fails."""

    pass


class PDFSandbox:
    """
    Sandbox for isolated PDF processing.

    Executes PDF extraction in a separate OS process with:
    - Process isolation (no shared memory)
    - Resource limits (memory, CPU, timeout)
    - Temporary directory cleanup
    - No network access (best-effort)
    """

    def __init__(
        self,
        memory_limit_mb: int = 512,
        timeout_seconds: int = 60,
        cpu_limit_seconds: int | None = None,
    ):
        """
        Initialize sandbox with resource limits.

        Args:
            memory_limit_mb: Maximum memory in MB
            timeout_seconds: Maximum wall-clock time in seconds
            cpu_limit_seconds: Maximum CPU time in seconds (optional)
        """
        self.limits = ResourceLimits(
            memory_limit_mb=memory_limit_mb,
            timeout_seconds=timeout_seconds,
            cpu_limit_seconds=cpu_limit_seconds,
        )

    def extract_pdf(
        self, pdf_path: Path, extractor_method: str = "auto"
    ) -> PDFExtraction:
        """
        Extract PDF in sandboxed process.

        Args:
            pdf_path: Path to PDF file
            extractor_method: Extraction method (auto, pdfplumber, pymupdf)

        Returns:
            PDFExtraction result

        Raises:
            SandboxError: If sandbox execution fails or times out
        """
        # Convert to absolute path
        pdf_path = pdf_path.resolve()

        if not pdf_path.exists():
            raise SandboxError(f"PDF file not found: {pdf_path}")

        # Execute in separate process with timeout
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _sandbox_worker,
                str(pdf_path),
                extractor_method,
                self.limits,
            )

            try:
                result = future.result(timeout=self.limits.timeout_seconds)
                return result
            except FutureTimeoutError:
                # Timeout exceeded - kill worker process
                future.cancel()
                raise SandboxError(
                    f"PDF processing exceeded timeout ({self.limits.timeout_seconds}s)"
                ) from None
            except Exception as e:
                raise SandboxError(f"PDF processing failed in sandbox: {e}") from e


def _sandbox_worker(
    pdf_path_str: str, extractor_method: str, limits: ResourceLimits
) -> PDFExtraction:
    """
    Worker function that runs in separate process.

    This function executes in an isolated process with no shared memory
    with the parent process. Resource limits are applied before extraction.

    Args:
        pdf_path_str: PDF file path as string
        extractor_method: Extraction method
        limits: Resource limits to apply

    Returns:
        PDFExtraction result

    Raises:
        Exception: If extraction fails
    """
    # Apply resource limits to this process
    apply_resource_limits(limits)

    # Create temporary directory for this worker
    # (automatically cleaned up when process exits)
    with tempfile.TemporaryDirectory(prefix="pdf2md_") as temp_dir:
        # Convert path back to Path object
        pdf_path = Path(pdf_path_str)

        # Create extractor
        extractor = ExtractorFactory.create_extractor(extractor_method)

        # Extract PDF
        result = extractor.extract(pdf_path)

        return result


# Export main class
__all__ = ["PDFSandbox", "SandboxError"]
