"""PDF conversion endpoint."""

import shutil
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from pdf2md.api.dependencies import get_current_user, get_job_queue
from pdf2md.auth.models import User
from pdf2md.auth.permissions import Permission, check_permission
from pdf2md.jobs.queue import JobQueue

router = APIRouter()


class ConvertResponse(BaseModel):
    """Response for convert endpoint."""

    job_id: str
    status: str


@router.post("/convert", response_model=ConvertResponse)
async def convert_pdf(
    file: Annotated[UploadFile, File(description="PDF file to convert")],
    output_format: Annotated[str, Form(description="Output format")] = "markdown",
    extractor: Annotated[str, Form(description="Extractor backend")] = "pdfplumber",
    include_metadata: Annotated[bool, Form(description="Include metadata")] = True,
    user: User = Depends(get_current_user),
    job_queue: JobQueue = Depends(get_job_queue),
) -> ConvertResponse:
    """
    Convert PDF to Markdown.
    
    Creates a background job for PDF conversion.
    
    Permissions: admin, job_manager, job_writer
    
    Args:
        file: PDF file to convert
        output_format: Output format (markdown, json, yaml, text)
        extractor: Extractor backend (pdfplumber, pymupdf)
        include_metadata: Whether to include metadata
        user: Current authenticated user
        job_queue: Job queue instance
        
    Returns:
        Job ID and initial status
        
    Raises:
        HTTPException: If user lacks permission or file is invalid
    """
    # Check permission
    if not check_permission(user, Permission.CREATE_JOB):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{user.role.value}' does not have permission to create jobs",
        )

    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File name is required"
        )

    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are supported"
        )

    # Validate output format
    listValidFormats = ["markdown", "json", "yaml", "text"]
    if output_format not in listValidFormats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid output format. Must be one of: {', '.join(listValidFormats)}",
        )

    # Validate extractor
    listValidExtractors = ["pdfplumber", "pymupdf"]
    if extractor not in listValidExtractors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid extractor. Must be one of: {', '.join(listValidExtractors)}",
        )

    # Save uploaded file
    strUploadsDir = "data/uploads"
    Path(strUploadsDir).mkdir(parents=True, exist_ok=True)

    strPdfPath = f"{strUploadsDir}/{user.strUserId}_{file.filename}"
    with open(strPdfPath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create job
    dictOptions = {
        "output_format": output_format,
        "extractor": extractor,
        "include_metadata": include_metadata,
    }

    strJobId = await job_queue.create_job(user.strUserId, strPdfPath, dictOptions)

    return ConvertResponse(job_id=strJobId, status="PENDING")
