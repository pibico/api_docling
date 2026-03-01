#!/usr/bin/env python3
"""
Application configuration using Pydantic settings.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings
from pathlib import Path
import secrets

class Settings(BaseSettings):
    # Project Info
    PROJECT_NAME: str = "Docling Document Converter API Service"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI service for document conversion to Markdown using Docling with PaddleOCR support"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    API_KEYS: List[str] = Field(default_factory=list)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    JWT_ALGORITHM: str = "HS256"

    # Docling Configuration
    DOCLING_USE_GPU: bool = True  # Enable GPU acceleration for Docling
    DOCLING_DEVICE: str = "cuda"  # cuda or cpu
    DOCLING_DO_OCR: bool = True  # Enable OCR for scanned documents
    DOCLING_DO_TABLE_STRUCTURE: bool = True  # Enable table structure detection
    DOCLING_OCR_LANGUAGES: List[str] = ["en", "es", "fr", "de"]  # OCR languages

    # External Service URLs
    PADDLEOCR_URL: str = "http://localhost:6951/api/v1"  # PaddleOCR API URL
    PADDLEOCR_API_KEY: str = "mi-paddleocr"  # PaddleOCR API Key for authentication
    OLLAMA_URL: str = "http://localhost:11434"  # Ollama API URL for LLM extraction

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 6952  # Port for api_docling
    WORKERS: int = 1
    RELOAD: bool = False
    ROOT_PATH: str = ""  # Set to /docling when behind nginx proxy

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    LOGS_DIR: Path = BASE_DIR / "logs"
    DOCLING_TEMP_DIR: Path = BASE_DIR / "docling_temp"
    DOCLING_UPLOADS_DIR: Path = BASE_DIR / "docling_uploads"
    DOCLING_RESULTS_DIR: Path = BASE_DIR / "docling_results"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "docling_api.log"

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 20  # Lower for document conversion operations
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # File Upload
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt",
        ".txt", ".html", ".md", ".rtf"
    ]

    # Document Processing
    DOCLING_MAX_PAGES: Optional[int] = None  # Limit pages to process (None = unlimited)
    DOCLING_BATCH_SIZE: int = 1  # Number of documents to process in parallel

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories if they don't exist
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.DOCLING_TEMP_DIR.mkdir(exist_ok=True)
        self.DOCLING_UPLOADS_DIR.mkdir(exist_ok=True)
        self.DOCLING_RESULTS_DIR.mkdir(exist_ok=True)

# Create settings instance
settings = Settings()
