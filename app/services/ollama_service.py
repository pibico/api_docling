#!/usr/bin/env python3
"""
Ollama service with connection pooling and request management.
"""
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from logzero import logger

from app.core.config import settings


class OllamaService:
    """Singleton service for Ollama API calls with connection pooling"""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self._initialized = False
        # Semaphore to limit concurrent requests to Ollama
        self._semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
        self._request_count = 0
        self._error_count = 0

    async def initialize(self):
        """Initialize the HTTP client with connection pooling"""
        if self._initialized:
            return

        try:
            # Create persistent client with connection pooling
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=10.0),  # 300s for generation, 10s for connect
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                    keepalive_expiry=30.0
                ),
                follow_redirects=True
            )
            self._initialized = True
            logger.info("Ollama service initialized with connection pooling")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama service: {e}")
            raise

    async def cleanup(self):
        """Cleanup HTTP client connections"""
        if self.client:
            await self.client.aclose()
            self._initialized = False
            logger.info(f"Ollama service cleaned up. Total requests: {self._request_count}, Errors: {self._error_count}")

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.1,
        stream: bool = False,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate text using Ollama model.

        Args:
            model: Model name (e.g., 'qwen2.5:7b')
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            stream: Whether to stream the response
            system: Optional system message

        Returns:
            Dictionary with 'response' and metadata

        Raises:
            HTTPException: If request fails
        """
        if not self._initialized:
            await self.initialize()

        # Use semaphore to limit concurrent requests
        async with self._semaphore:
            start_time = datetime.now()
            self._request_count += 1

            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "temperature": temperature
                }

                if system:
                    payload["system"] = system

                logger.info(f"Ollama generate request #{self._request_count}: model={model}, prompt_len={len(prompt)}")

                response = await self.client.post(
                    f"{settings.OLLAMA_URL}/api/generate",
                    json=payload
                )

                response.raise_for_status()

                result = response.json()
                duration = (datetime.now() - start_time).total_seconds()

                logger.info(f"Ollama generate completed in {duration:.2f}s")

                return result

            except httpx.TimeoutException as e:
                self._error_count += 1
                logger.error(f"Ollama request timeout after {(datetime.now() - start_time).total_seconds():.2f}s: {e}")
                raise
            except httpx.HTTPStatusError as e:
                self._error_count += 1
                logger.error(f"Ollama HTTP error {e.response.status_code}: {e}")
                raise
            except Exception as e:
                self._error_count += 1
                logger.error(f"Ollama request error: {e}", exc_info=True)
                raise

    async def extract_json(
        self,
        model: str,
        markdown: str,
        instructions: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Extract structured JSON from markdown using LLM.

        Args:
            model: Model name
            markdown: Markdown content to extract from
            instructions: Extraction instructions
            temperature: Sampling temperature

        Returns:
            Dictionary with extraction results and metadata
        """
        try:
            prompt = f"{instructions}\n\nDocument content:\n{markdown}"

            result = await self.generate(
                model=model,
                prompt=prompt,
                temperature=temperature,
                stream=False
            )

            extraction_text = result.get("response", "")

            # Try to parse as JSON
            try:
                json_data = json.loads(extraction_text)
                return {
                    "status": "success",
                    "extraction": json_data,
                    "model": model,
                    "markdown_length": len(markdown),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "total_duration": result.get("total_duration")
                }
            except json.JSONDecodeError:
                # Return raw extraction if not valid JSON
                return {
                    "status": "partial",
                    "raw_extraction": extraction_text,
                    "model": model,
                    "markdown_length": len(markdown),
                    "prompt_eval_count": result.get("prompt_eval_count"),
                    "eval_count": result.get("eval_count"),
                    "total_duration": result.get("total_duration")
                }

        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "model": model,
                "markdown_length": len(markdown)
            }

    async def check_health(self) -> bool:
        """Check if Ollama service is healthy"""
        if not self._initialized:
            return False

        try:
            response = await self.client.get(
                f"{settings.OLLAMA_URL}/api/tags",
                timeout=5.0
            )
            return response.status_code == 200
        except:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "initialized": self._initialized,
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1) * 100
        }


# Create singleton instance
ollama_service = OllamaService()
