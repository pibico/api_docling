#!/usr/bin/env python3
"""
API router aggregation.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import health, docling, web

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    docling.router,
    tags=["Conversion"]
)

api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    web.router,
    tags=["Web Interface"]
)
