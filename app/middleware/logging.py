#!/usr/bin/env python3
"""
Logging middleware for request/response tracking.
"""
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logzero import logger


async def logging_middleware(request: Request, call_next):
    """
    Log all incoming requests and outgoing responses.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Track request time
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} "
        f"completed with status {response.status_code} in {duration:.3f}s"
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response
