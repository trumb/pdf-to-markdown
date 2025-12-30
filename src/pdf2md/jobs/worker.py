"""Background job worker."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from pdf2md.core.converter import PDFConverter
from pdf2md.jobs.models import JobStatus
from pdf2md.jobs.queue import JobQueue

logger = logging.getLogger(__name__)


class JobWorker:
    """
    Background worker that processes PDF conversion jobs.
    
    Runs independently of API authentication. Jobs continue to completion
    even if the token that created them is revoked.
    """

    def __init__(
        self, jobQueue: JobQueue, strResultsDir: str, floatPollInterval: float = 1.0
    ) -> None:
        """
        Initialize job worker.
        
        Args:
            jobQueue: Job queue instance
            strResultsDir: Directory to store result files
            floatPollInterval: Seconds between queue polls
        """
        self.jobQueue: JobQueue = jobQueue
        self.strResultsDir: str = strResultsDir
        self.floatPollInterval: float = floatPollInterval
        self.boolRunning: bool = False
        self.optTask: Optional[asyncio.Task[None]] = None

        # Create results directory
        Path(strResultsDir).mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the background worker."""
        if self.boolRunning:
            logger.warning("Worker already running")
            return

        self.boolRunning = True
        self.optTask = asyncio.create_task(self._worker_loop())
        logger.info("Job worker started")

    async def stop(self) -> None:
        """Stop the background worker."""
        if not self.boolRunning:
            return

        self.boolRunning = False

        if self.optTask:
            await self.optTask
            self.optTask = None

        logger.info("Job worker stopped")

    async def _worker_loop(self) -> None:
        """Main worker loop."""
        while self.boolRunning:
            try:
                # Get next pending job
                optJob = await self._get_next_job()

                if optJob:
                    await self._process_job(optJob.strJobId)
                else:
                    # No jobs available, wait before polling again
                    await asyncio.sleep(self.floatPollInterval)

            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(self.floatPollInterval)

    async def _get_next_job(self) -> Optional[any]:
        """
        Get next pending job from queue.
        
        Returns:
            Job object or None if no jobs available
        """
        listJobs, _ = await self.jobQueue.list_jobs(
            optStatus=JobStatus.PENDING, intLimit=1, intOffset=0
        )

        if not listJobs:
            return None

        job = listJobs[0]

        # Skip throttled jobs
        if job.boolThrottled:
            return None

        return job

    async def _process_job(self, strJobId: str) -> None:
        """
        Process a PDF conversion job.
        
        Args:
            strJobId: Job ID to process
        """
        try:
            # Get job details
            optJob = await self.jobQueue.get_job(strJobId)
            if optJob is None:
                logger.error(f"Job {strJobId} not found")
                return

            logger.info(f"Processing job {strJobId}: {optJob.strPdfPath}")

            # Update status to RUNNING
            await self.jobQueue.update_job_status(strJobId, JobStatus.RUNNING)

            # Parse job options
            dictOptions = json.loads(optJob.strOptions)

            # Convert PDF using Phase 1 converter
            converter = PDFConverter()
            strResult = await asyncio.to_thread(
                self._convert_pdf_sync, converter, optJob.strPdfPath, dictOptions
            )

            # Save result
            strResultPath = str(Path(self.strResultsDir) / f"{strJobId}.md")
            Path(strResultPath).write_text(strResult, encoding="utf-8")

            # Update status to COMPLETED
            await self.jobQueue.update_job_status(
                strJobId, JobStatus.COMPLETED, optResultPath=strResultPath
            )

            logger.info(f"Job {strJobId} completed successfully")

        except Exception as e:
            logger.error(f"Job {strJobId} failed: {e}", exc_info=True)

            # Update status to FAILED
            await self.jobQueue.update_job_status(
                strJobId, JobStatus.FAILED, optErrorMessage=str(e)
            )

    def _convert_pdf_sync(
        self, converter: PDFConverter, strPdfPath: str, dictOptions: dict[str, any]
    ) -> str:
        """
        Synchronous PDF conversion wrapper.
        
        Args:
            converter: PDFConverter instance
            strPdfPath: Path to PDF file
            dictOptions: Conversion options
            
        Returns:
            Markdown result string
        """
        # Extract options
        strOutputFormat = dictOptions.get("output_format", "markdown")
        strExtractorBackend = dictOptions.get("extractor", "pdfplumber")
        boolIncludeMetadata = dictOptions.get("include_metadata", True)

        # Convert PDF
        return converter.convert(
            pdf_path=strPdfPath,
            output_format=strOutputFormat,
            extractor_backend=strExtractorBackend,
            include_metadata=boolIncludeMetadata,
        )