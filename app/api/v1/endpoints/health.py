#!/usr/bin/env python3
"""
Health check endpoint.
"""
from fastapi import APIRouter
from datetime import datetime
import httpx

from app.core.config import settings
from app.services import docling_service

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint with external service status.
    """
    # Check PaddleOCR availability
    paddleocr_status = "unavailable"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.PADDLEOCR_URL}/health", timeout=2)
            if response.status_code == 200:
                paddleocr_status = "available"
    except:
        pass

    # Check Ollama availability
    ollama_status = "unavailable"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                ollama_status = "available"
    except:
        pass

    return {
        "status": "healthy",
        "service": "Docling Document Converter",
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
        "gpu_available": docling_service.is_gpu_available(),
        "docling_initialized": docling_service.is_initialized,
        "external_services": {
            "paddleocr": paddleocr_status,
            "ollama": ollama_status
        },
        "configuration": {
            "max_upload_size": f"{settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            "allowed_extensions": settings.ALLOWED_UPLOAD_EXTENSIONS,
            "use_gpu": settings.DOCLING_USE_GPU,
            "ocr_enabled": settings.DOCLING_DO_OCR,
            "table_detection": settings.DOCLING_DO_TABLE_STRUCTURE
        }
    }
