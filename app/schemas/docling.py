#!/usr/bin/env python3
"""
Pydantic schemas for Docling document conversion.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ConversionRequest(BaseModel):
    """Request model for base64 file conversion"""
    file_content: str = Field(..., description="Base64 encoded file content")
    filename: str = Field(..., description="Original filename with extension")
    use_ocr: bool = Field(True, description="Use OCR for scanned PDFs")
    detect_tables: bool = Field(True, description="Detect and format tables")
    ocr_language: str = Field("en", description="OCR language (en, es, fr, etc.)")


class ConversionResponse(BaseModel):
    """Response model for document conversion"""
    markdown: str = Field(..., description="Converted markdown content")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Conversion status")
    pages: Optional[int] = Field(None, description="Number of pages (for PDFs)")
    tables_detected: Optional[int] = Field(None, description="Number of tables detected")
    ocr_used: bool = Field(False, description="Whether OCR was used")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class TaskResponse(BaseModel):
    """Response for async task creation"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """Response for async task status check"""
    task_id: str
    status: str  # pending, processing, completed, error
    progress: Optional[int] = None  # percentage 0-100
    filename: Optional[str] = None
    markdown: Optional[str] = None
    pages: Optional[int] = None
    tables_detected: Optional[int] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class ExtractionRequest(BaseModel):
    """Request for LLM extraction"""
    model: str = Field("qwen2.5:7b", description="Ollama model to use")
    instructions: Optional[str] = Field(None, description="Custom extraction instructions")


class ExtractionResponse(BaseModel):
    """Response for LLM extraction"""
    status: str
    markdown_length: int
    extraction: Optional[Dict[str, Any]] = None
    raw_extraction: Optional[str] = None
    model: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    status_code: Optional[int] = None
