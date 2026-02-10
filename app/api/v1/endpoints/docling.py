#!/usr/bin/env python3
"""
Docling document conversion endpoints.
"""
import base64
import tempfile
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Form, Depends
from pydantic import BaseModel, Field
from logzero import logger

from app.core.config import settings
from app.api.v1.dependencies.auth import verify_api_key
from app.schemas.docling import (
    ConversionRequest,
    ConversionResponse,
    TaskResponse,
    TaskStatusResponse,
    ExtractionResponse
)
from app.services import docling_service, task_storage
from app.services.ollama_service import ollama_service

router = APIRouter()


@router.post("/convert", response_model=ConversionResponse, tags=["Conversion"])
async def convert_document_base64(
    request: ConversionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Convert base64 encoded document to Markdown.

    - **file_content**: Base64 encoded file content
    - **filename**: Original filename with extension
    - **use_ocr**: Enable OCR for scanned PDFs (default: true)
    - **detect_tables**: Detect and format tables (default: true)
    - **ocr_language**: OCR language code (default: en)
    """
    temp_file = None
    try:
        # Decode base64 content
        try:
            file_content = base64.b64decode(request.file_content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 content: {e}")

        # Check file size
        if len(file_content) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/1024/1024}MB"
            )

        # Save to temporary file
        suffix = Path(request.filename).suffix
        if not suffix:
            suffix = '.pdf'  # Default to PDF

        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
            dir=settings.DOCLING_TEMP_DIR
        )
        temp_file.write(file_content)
        temp_file.close()

        temp_path = Path(temp_file.name)

        # Convert document
        result = await docling_service.convert_document(
            temp_path,
            use_ocr=request.use_ocr,
            detect_tables=request.detect_tables
        )

        return ConversionResponse(
            markdown=result["markdown"],
            filename=request.filename,
            status=result["status"],
            pages=result.get("pages"),
            tables_detected=result.get("tables_detected"),
            ocr_used=result.get("ocr_used", False),
            processing_time=result.get("processing_time", 0),
            metadata=result.get("metadata")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file and Path(temp_file.name).exists():
            try:
                Path(temp_file.name).unlink()
            except:
                pass


@router.post("/convert/file", response_model=ConversionResponse, tags=["Conversion"])
async def convert_file(
    file: UploadFile = File(...),
    use_ocr: bool = Form(True),
    detect_tables: bool = Form(True),
    ocr_language: str = Form("en"),
    api_key: str = Depends(verify_api_key)
):
    """
    Convert uploaded file to Markdown.

    - **file**: File to convert (PDF, DOCX, XLSX, etc.)
    - **use_ocr**: Enable OCR for scanned documents
    - **detect_tables**: Enable table detection
    - **ocr_language**: OCR language code
    """
    temp_file_path = None
    try:
        # Check file extension
        suffix = Path(file.filename).suffix.lower()
        if suffix not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )

        # Check file size
        contents = await file.read()
        if len(contents) > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE/1024/1024}MB"
            )

        # Save uploaded file
        temp_file_path = settings.DOCLING_TEMP_DIR / f"upload_{datetime.now().timestamp()}{suffix}"

        with open(temp_file_path, 'wb') as f:
            f.write(contents)

        # Convert document
        result = await docling_service.convert_document(
            temp_file_path,
            use_ocr=use_ocr,
            detect_tables=detect_tables
        )

        return ConversionResponse(
            markdown=result["markdown"],
            filename=file.filename,
            status=result["status"],
            pages=result.get("pages"),
            tables_detected=result.get("tables_detected"),
            ocr_used=result.get("ocr_used", False),
            processing_time=result.get("processing_time", 0),
            metadata=result.get("metadata")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File conversion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass


@router.post("/convert-async", response_model=TaskResponse, tags=["Conversion"])
async def convert_pdf_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_ocr: bool = Form(True),
    detect_tables: bool = Form(True),
    api_key: str = Depends(verify_api_key)
):
    """
    Convert PDF to Markdown asynchronously (for large documents).

    Returns a task_id to check progress via /task/{task_id}

    - **file**: PDF file to convert
    - **use_ocr**: Enable OCR for scanned PDFs (default: true)
    - **detect_tables**: Detect and format tables (default: true)
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save file to persistent location
    upload_dir = settings.DOCLING_UPLOADS_DIR
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f"{task_id}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create task entry in Redis
    task_storage.create_task(task_id, {
        "status": "pending",
        "progress": 0,
        "filename": file.filename,
        "file_path": str(file_path),
        "use_ocr": use_ocr,
        "detect_tables": detect_tables
    })

    # Start background processing
    background_tasks.add_task(process_pdf_background, task_id)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task created. Check status at /task/{task_id}"
    )


@router.post("/convert-document-async", response_model=TaskResponse, tags=["Conversion"])
async def convert_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_ocr: bool = Form(True),
    detect_tables: bool = Form(True),
    api_key: str = Depends(verify_api_key)
):
    """
    Convert document to Markdown asynchronously (for large DOCX, XLSX, PPTX files).

    Returns a task_id to check progress via /task/{task_id}

    - **file**: Document file to convert (DOCX, XLSX, PPTX, etc. - excludes PDF)
    - **use_ocr**: Enable OCR for scanned documents (default: true)
    - **detect_tables**: Detect and format tables (default: true)
    """
    # Check file extension
    suffix = Path(file.filename).suffix.lower()

    # Reject PDF files (use /convert-async endpoint instead)
    if suffix == '.pdf':
        raise HTTPException(
            status_code=400,
            detail="PDF files should use /convert-async endpoint instead."
        )

    # Check if file type is allowed
    if suffix not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        allowed_non_pdf = [ext for ext in settings.ALLOWED_UPLOAD_EXTENSIONS if ext != '.pdf']
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_non_pdf)}"
        )

    # Generate unique task ID
    task_id = str(uuid.uuid4())

    # Save file to persistent location
    upload_dir = settings.DOCLING_UPLOADS_DIR
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / f"{task_id}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Create task entry in Redis
    task_storage.create_task(task_id, {
        "status": "pending",
        "progress": 0,
        "filename": file.filename,
        "file_path": str(file_path),
        "use_ocr": use_ocr,
        "detect_tables": detect_tables
    })

    # Start background processing
    background_tasks.add_task(process_document_background, task_id)

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task created. Check status at /task/{task_id}"
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse, tags=["Conversion"])
async def get_task_status(task_id: str):
    """Get the status of an async conversion task"""
    task = task_storage.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(**task)


class MarkdownExtractionRequest(BaseModel):
    """Request for markdown extraction"""
    markdown: str = Field(..., description="Markdown content to extract from")
    model: str = Field("qwen2.5:7b", description="Ollama model to use")
    instructions: Optional[str] = Field(None, description="Custom extraction instructions")


@router.post("/extract-markdown", tags=["Extraction"])
async def extract_from_markdown(
    request: MarkdownExtractionRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Extract structured data from markdown using Ollama LLM.

    - **markdown**: Markdown content to extract from
    - **model**: Ollama model to use (default: qwen2.5:7b)
    - **instructions**: Custom extraction instructions (optional)
    """
    try:
        markdown_content = request.markdown
        model = request.model
        instructions = request.instructions

        # If custom instructions not provided, use default
        if not instructions:
            instructions_file = settings.BASE_DIR / "instructions.txt"
            if instructions_file.exists():
                with open(instructions_file, 'r') as f:
                    instructions = f.read()
            else:
                instructions = """Extract authorization data and return ONLY valid JSON with this structure:
{
  "lw_dossier": {...},
  "lw_authorization_points": [...],
  "lw_parameters": [...]
}"""

        # Call Ollama for extraction using singleton service with connection pooling
        result = await ollama_service.extract_json(
            model=model,
            markdown=markdown_content,
            instructions=instructions,
            temperature=0.1
        )

        # Return the result (already formatted by ollama_service)
        return ExtractionResponse(**result)

    except httpx.TimeoutException as e:
        logger.error(f"Markdown extraction timeout: {e}")
        raise HTTPException(
            status_code=504,
            detail="Extraction timed out. The document may be too large or the LLM is busy. Please try again."
        )
    except Exception as e:
        logger.error(f"Markdown extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract", tags=["Extraction"])
async def extract_with_llm(
    file: UploadFile = File(...),
    model: str = Form("qwen2.5:7b"),
    instructions: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key)
):
    """
    Convert document and extract structured data using Ollama LLM.

    - **file**: Document file to convert and extract from
    - **model**: Ollama model to use (default: qwen2.5:7b)
    - **instructions**: Custom extraction instructions (optional)
    """
    try:
        # First convert to markdown
        response = await convert_file(
            file=file,
            use_ocr=True,
            detect_tables=True,
            ocr_language="es",
            api_key=api_key
        )

        markdown_content = response.markdown

        # If custom instructions not provided, use default
        if not instructions:
            instructions_file = settings.BASE_DIR / "instructions.txt"
            if instructions_file.exists():
                with open(instructions_file, 'r') as f:
                    instructions = f.read()
            else:
                instructions = """Extract authorization data and return ONLY valid JSON with this structure:
{
  "lw_dossier": {...},
  "lw_authorization_points": [...],
  "lw_parameters": [...]
}"""

        # Call Ollama for extraction using singleton service with connection pooling
        result = await ollama_service.extract_json(
            model=model,
            markdown=markdown_content,
            instructions=instructions,
            temperature=0.1
        )

        # Return the result (already formatted by ollama_service)
        return ExtractionResponse(**result)

    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_pdf_background(task_id: str):
    """Background task to process PDF conversion"""
    file_path = None
    try:
        task = task_storage.get_task(task_id)
        if task is None:
            logger.error(f"Task {task_id} not found in storage")
            return

        task_storage.update_task(task_id, {
            "status": "processing",
            "progress": 10
        })

        file_path = Path(task["file_path"])
        use_ocr = task["use_ocr"]
        detect_tables = task["detect_tables"]

        task_storage.update_task(task_id, {"progress": 30})

        # Convert document
        result = await docling_service.convert_document(
            file_path,
            use_ocr=use_ocr,
            detect_tables=detect_tables
        )

        task_storage.update_task(task_id, {
            "status": "completed",
            "progress": 100,
            "markdown": result["markdown"],
            "pages": result.get("pages"),
            "tables_detected": result.get("tables_detected"),
            "completed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        task_storage.update_task(task_id, {
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

    finally:
        # Clean up file after processing
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except:
            pass


async def process_document_background(task_id: str):
    """Background task to process document conversion (non-PDF)"""
    file_path = None
    try:
        task = task_storage.get_task(task_id)
        if task is None:
            logger.error(f"Task {task_id} not found in storage")
            return

        task_storage.update_task(task_id, {
            "status": "processing",
            "progress": 10
        })

        file_path = Path(task["file_path"])
        use_ocr = task["use_ocr"]
        detect_tables = task["detect_tables"]

        task_storage.update_task(task_id, {"progress": 30})

        # Convert document
        result = await docling_service.convert_document(
            file_path,
            use_ocr=use_ocr,
            detect_tables=detect_tables
        )

        task_storage.update_task(task_id, {
            "status": "completed",
            "progress": 100,
            "markdown": result["markdown"],
            "pages": result.get("pages"),
            "tables_detected": result.get("tables_detected"),
            "completed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error processing task {task_id}: {e}")
        task_storage.update_task(task_id, {
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now().isoformat()
        })

    finally:
        # Clean up file after processing
        try:
            if file_path and file_path.exists():
                file_path.unlink()
        except:
            pass
