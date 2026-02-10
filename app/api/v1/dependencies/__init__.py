#!/usr/bin/env python3
"""
API dependencies package.
"""
from app.api.v1.dependencies.auth import verify_api_key

__all__ = ["verify_api_key"]
