#!/usr/bin/env python3
"""
Authentication dependencies.
"""
from fastapi import Header, HTTPException, status
from typing import Optional

from app.core.config import settings


async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify API key from request header.
    Optional authentication - can be enabled by adding API keys to settings.
    """
    # If no API keys configured, skip authentication
    if not settings.API_KEYS:
        return None

    # If API keys are configured, require valid key
    if not x_api_key or x_api_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )

    return x_api_key
