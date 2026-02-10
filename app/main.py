#!/usr/bin/env python3
"""
Main FastAPI application for Docling Document Converter Service.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from logzero import logger
import logzero
import logging
from pathlib import Path
import mimetypes
import os

from app.api.v1.api import api_router
from app.core.config import settings
from app.middleware import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    logging_middleware
)
from app.services import docling_service
from app.services.ollama_service import ollama_service


# Configure logging
logzero.logfile(
    settings.LOGS_DIR / settings.LOG_FILE,
    maxBytes=1e6,
    backupCount=3
)
logzero.loglevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("=" * 60)
    logger.info("Starting Docling Document Converter API Service...")
    logger.info(f"Version: {settings.VERSION}")
    logger.info(f"Port: {settings.PORT}")
    logger.info("=" * 60)

    try:
        # Initialize Docling service
        await docling_service.initialize()
        logger.info("Docling service initialized successfully")

        # Initialize Ollama service
        await ollama_service.initialize()
        logger.info("Ollama service initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    logger.info("Docling API Service started successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down Docling Document Converter API Service...")

    # Cleanup Ollama service
    await ollama_service.cleanup()

    # Cleanup GPU resources
    docling_service.cleanup()

    logger.info("Docling API Service shut down successfully")
    logger.info("=" * 60)


# Create FastAPI app
# Note: When behind a proxy, set ROOT_PATH env var to /docling
root_path = os.getenv('ROOT_PATH', '')

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    root_path=root_path,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,  # We'll create a custom docs endpoint
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
    servers=[{"url": root_path}] if root_path else None
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Add custom middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Custom Swagger UI endpoint with correct OpenAPI URL
@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    """Custom Swagger UI that works with root_path."""
    openapi_url = f"{root_path}{settings.API_V1_STR}/openapi.json"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
        <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
        <title>{settings.PROJECT_NAME} - Swagger UI</title>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
        const ui = SwaggerUIBundle({{
            url: '{openapi_url}',
            dom_id: '#swagger-ui',
            layout: 'BaseLayout',
            deepLinking: true,
            showExtensions: true,
            showCommonExtensions: true,
            oauth2RedirectUrl: window.location.origin + '{root_path}/docs/oauth2-redirect',
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIBundle.SwaggerUIStandalonePreset
            ],
        }})
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# Include API routers FIRST
app.include_router(api_router, prefix=settings.API_V1_STR)

# Include web interface at root
from app.api.v1.endpoints import web
app.include_router(web.router)

# Mount static files
static_path = Path(__file__).parent.parent / "static"

# Serve static files with FileResponse as workaround for mount issues
@app.get("/static/{file_path:path}")
@app.head("/static/{file_path:path}")
async def serve_static(file_path: str):
    """Serve static files."""
    full_path = static_path / file_path
    if full_path.exists() and full_path.is_file():
        # Get mime type with custom mappings
        mime_type, _ = mimetypes.guess_type(str(full_path))

        # Add custom MIME types for ES6 modules
        if file_path.endswith('.mjs'):
            mime_type = 'application/javascript'
        elif file_path.endswith('.wasm'):
            mime_type = 'application/wasm'
        elif file_path.endswith('.onnx'):
            mime_type = 'application/octet-stream'

        return FileResponse(full_path, media_type=mime_type)

    return JSONResponse(content={"error": "File not found"}, status_code=404)

logger.info(f"Static files served from: {static_path}")


# Store service in app state for dependency injection
app.state.docling_service = docling_service
