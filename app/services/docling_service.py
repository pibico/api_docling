#!/usr/bin/env python3
"""
Docling document conversion service.
"""
import io
import base64
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

import httpx
import pypdfium2 as pdfium
from logzero import logger

from app.core.config import settings


class DoclingService:
    """Service for document conversion using Docling"""

    def __init__(self):
        self.converter = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the Docling converter"""
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
            from docling.datamodel.accelerator_options import AcceleratorOptions

            # Configure pipeline with GPU acceleration
            pipeline_options = PdfPipelineOptions(
                accelerator_options=AcceleratorOptions(
                    device=settings.DOCLING_DEVICE,
                    num_threads=4
                ),
                do_ocr=settings.DOCLING_DO_OCR,
                do_table_structure=settings.DOCLING_DO_TABLE_STRUCTURE,
                ocr_options=EasyOcrOptions(
                    use_gpu=settings.DOCLING_USE_GPU,
                    lang=settings.DOCLING_OCR_LANGUAGES
                )
            )

            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            self.is_initialized = True
            logger.info("Docling service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Docling service: {e}")
            self.is_initialized = False
            raise

    def cleanup(self):
        """Cleanup resources"""
        self.converter = None
        self.is_initialized = False
        logger.info("Docling service cleaned up")

    def is_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    async def convert_document(
        self,
        file_path: Path,
        use_ocr: bool = True,
        detect_tables: bool = True
    ) -> Dict[str, Any]:
        """
        Convert document to markdown using Docling

        Args:
            file_path: Path to document file
            use_ocr: Enable OCR for scanned documents
            detect_tables: Enable table detection

        Returns:
            Dictionary with conversion results
        """
        start_time = datetime.now()
        ocr_used = False

        try:
            if not self.is_initialized:
                raise RuntimeError("Docling service not initialized")

            # Try Docling conversion first
            try:
                logger.info(f"Converting document with Docling: {file_path.name}")
                result = self.converter.convert(str(file_path))
                markdown_content = result.document.export_to_markdown()

                # Check if mostly images (indicates scanned document)
                if markdown_content.count("<!-- image -->") > 5 and len(markdown_content) < 500:
                    raise ValueError("Document appears to be scanned")

                # Get metadata
                pages = len(result.document.pages) if hasattr(result.document, 'pages') else 0
                tables_count = len(result.document.tables) if hasattr(result.document, 'tables') else 0

                processing_time = (datetime.now() - start_time).total_seconds()

                return {
                    "markdown": markdown_content,
                    "pages": pages,
                    "tables_detected": tables_count,
                    "ocr_used": False,
                    "processing_time": processing_time,
                    "metadata": {
                        "title": getattr(result.document, 'title', None),
                        "language": getattr(result.document, 'language', None),
                    },
                    "status": "success"
                }

            except Exception as e:
                logger.info(f"Docling conversion failed, trying OCR fallback: {e}")

                if not use_ocr:
                    raise RuntimeError(
                        "Document appears to be scanned but OCR is disabled"
                    )

                # Fallback to OCR
                markdown_content, tables_count = await self._process_with_ocr(
                    file_path,
                    file_path.name,
                    detect_tables
                )
                ocr_used = True

                processing_time = (datetime.now() - start_time).total_seconds()

                return {
                    "markdown": markdown_content,
                    "pages": None,
                    "tables_detected": tables_count,
                    "ocr_used": True,
                    "processing_time": processing_time,
                    "metadata": None,
                    "status": "success"
                }

        except Exception as e:
            logger.error(f"Error converting document: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            raise

    async def _process_with_ocr(
        self,
        pdf_path: Path,
        filename: str,
        detect_tables: bool = True
    ) -> Tuple[str, int]:
        """
        Process PDF with OCR using PaddleOCR API

        Args:
            pdf_path: Path to PDF file
            filename: Original filename
            detect_tables: Enable table detection

        Returns:
            Tuple of (markdown_content, tables_count)
        """
        pdf = pdfium.PdfDocument(str(pdf_path))
        n_pages = len(pdf)

        markdown_content = f"# {Path(filename).stem}\n"
        tables_count = 0

        for page_num in range(n_pages):
            logger.info(f"Processing page {page_num + 1}/{n_pages} with OCR...")

            # Render page
            page = pdf[page_num]
            pil_image = page.render(scale=2).to_pil()

            # Convert to bytes
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            buffered.seek(0)

            # Send to OCR API
            files = {'file': (f'page_{page_num + 1}.png', buffered, 'image/png')}

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.PADDLEOCR_URL}/ocr",
                        files=files,
                        headers={"X-API-Key": settings.PADDLEOCR_API_KEY},
                        timeout=30
                    )
                    response.raise_for_status()
                    ocr_result = response.json()

                # Process OCR results
                page_content, page_tables = self._format_ocr_results(
                    ocr_result,
                    page_num + 1,
                    detect_tables
                )

                markdown_content += page_content
                tables_count += page_tables

            except Exception as e:
                logger.error(f"OCR error on page {page_num + 1}: {e}")
                markdown_content += f"\n## Page {page_num + 1}\n\n_[Error processing this page]_\n"

        return markdown_content, tables_count

    def _format_ocr_results(
        self,
        ocr_result: dict,
        page_num: int,
        detect_tables: bool = True
    ) -> Tuple[str, int]:
        """
        Format OCR results with optional table detection

        Args:
            ocr_result: OCR API response
            page_num: Page number
            detect_tables: Enable table detection

        Returns:
            Tuple of (page_content, tables_found)
        """
        ocr_data = []

        # Extract OCR data
        if 'ocr_results' in ocr_result and ocr_result['ocr_results']:
            for page_result in ocr_result['ocr_results']:
                if page_result.get('page') == 1 and 'text' in page_result:
                    for line_data in page_result['text'][0]:
                        if len(line_data) >= 2:
                            bbox = line_data[0]
                            text_info = line_data[1]
                            text = text_info[0] if isinstance(text_info, list) else text_info

                            if text.strip():
                                ocr_data.append({
                                    'text': text.strip(),
                                    'x': bbox[0][0],
                                    'y': bbox[0][1],
                                    'bbox': bbox
                                })

        page_content = f"\n## Page {page_num}\n\n"
        tables_found = 0

        if not ocr_data:
            return page_content + "_[No text detected]_\n", 0

        # Sort by position
        ocr_data.sort(key=lambda item: (item['y'], item['x']))

        # Group into rows
        rows = self._group_into_rows(ocr_data)

        # Detect and format tables
        if detect_tables and self._is_table_structure(rows):
            page_content += self._format_as_table(rows)
            tables_found = 1
        else:
            page_content += self._format_as_text(rows)

        return page_content, tables_found

    def _group_into_rows(self, ocr_data, y_threshold=15):
        """Group OCR data into rows"""
        if not ocr_data:
            return []

        rows = []
        current_row = []
        current_y = ocr_data[0]['y']

        for item in ocr_data:
            if abs(item['y'] - current_y) <= y_threshold:
                current_row.append(item)
            else:
                if current_row:
                    current_row.sort(key=lambda x: x['x'])
                    rows.append(current_row)
                current_row = [item]
                current_y = item['y']

        if current_row:
            current_row.sort(key=lambda x: x['x'])
            rows.append(current_row)

        return rows

    def _is_table_structure(self, rows):
        """Check if rows form a table"""
        if len(rows) < 3:
            return False

        row_lengths = [len(row) for row in rows]
        avg_length = sum(row_lengths) / len(row_lengths)

        return avg_length > 2 and max(row_lengths) - min(row_lengths) <= 2

    def _format_as_table(self, rows):
        """Format rows as markdown table"""
        if not rows:
            return ""

        # Find max columns
        max_cols = max(len(row) for row in rows)

        # Build table
        markdown = ""
        for i, row in enumerate(rows):
            # Pad row to max columns
            cells = [item['text'] for item in row]
            cells.extend([''] * (max_cols - len(cells)))

            markdown += "| " + " | ".join(cells) + " |\n"

            # Add separator after header
            if i == 0:
                markdown += "| " + " | ".join(["-" * 3] * max_cols) + " |\n"

        return markdown + "\n"

    def _format_as_text(self, rows):
        """Format rows as regular text"""
        lines = []

        for row in rows:
            if len(row) == 1:
                lines.append(row[0]['text'])
            else:
                # Preserve spacing
                line = ""
                for i, item in enumerate(row):
                    if i > 0:
                        gap = item['x'] - row[i-1]['bbox'][1][0]
                        if gap > 50:
                            line += "    "
                        else:
                            line += " "
                    line += item['text']
                lines.append(line)

        return "\n".join(lines) + "\n"


# Create singleton instance
docling_service = DoclingService()
