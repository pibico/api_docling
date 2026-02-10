# Docling Document Converter Service

A FastAPI service that converts various document formats (PDF, DOCX, XLSX, PPTX) to Markdown with OCR support via PaddleOCR integration.

## Features

- **Multi-format support**: PDF, DOCX, XLSX, PPTX
- **OCR Integration**: Automatic detection of scanned PDFs with PaddleOCR fallback
- **Table Detection**: Preserves table structure in markdown format
- **LLM Integration**: Extract structured data using Ollama models
- **REST API**: Simple HTTP endpoints for document conversion

## Architecture

```
User Request → Docling API (Port 7002)
                    ↓
            Document Analysis
                    ↓
        ┌───────────┴───────────┐
        │                       │
    Text PDF               Scanned PDF
        │                       │
    Docling                PaddleOCR
    Converter              (Port 7001)
        │                       │
        └───────────┬───────────┘
                    ↓
            Markdown Output
                    ↓
            Ollama Models
            (Port 11434)
                    ↓
            Structured JSON
```

## Installation

The service is installed in `/home/erpnext/.www/projects/app/docling/` and uses the existing `fp16-env` environment.

### Dependencies
- docling
- fastapi
- uvicorn
- pypdfium2
- python-docx
- openpyxl
- requests

## Service Management

The service runs under Supervisor:

```bash
# Check status
sudo supervisorctl status docling

# Start/Stop/Restart
sudo supervisorctl start docling
sudo supervisorctl stop docling
sudo supervisorctl restart docling

# View logs
tail -f /home/erpnext/.www/projects/app/docling/logs/docling.log
```

## API Endpoints

### Health Check
```bash
GET http://localhost:7002/health
```

### Convert Document
```bash
POST http://localhost:7002/convert
```

Parameters:
- `file`: Document file (PDF, DOCX, etc.)
- `use_ocr`: Enable OCR for scanned documents (default: true)
- `detect_tables`: Detect and format tables (default: true)

### Extract Authorization Data
```bash
POST http://localhost:7002/extract
```

Parameters:
- `file`: Document file
- `model`: Ollama model to use (default: "qwen2.5:7b")
- `instructions`: Custom extraction instructions (optional)

## Usage Examples

### Convert PDF to Markdown
```python
import requests

with open('document.pdf', 'rb') as f:
    files = {'file': f}
    data = {'use_ocr': 'true', 'detect_tables': 'true'}
    
    response = requests.post(
        'http://localhost:7002/convert',
        files=files,
        data=data
    )
    
    result = response.json()
    markdown = result['markdown']
```

### Extract Structured Data
```python
with open('authorization.pdf', 'rb') as f:
    files = {'file': f}
    data = {'model': 'qwen2.5:7b'}
    
    response = requests.post(
        'http://localhost:7002/extract',
        files=files,
        data=data
    )
    
    result = response.json()
    extraction = result['extraction']  # Structured JSON data
```

## Integration with LeoWater

The service is designed to extract authorization data for the LeoWater system:

1. **Document Conversion**: PDFs are converted to markdown preserving structure
2. **Data Extraction**: LLM models extract specific fields:
   - Dossier information (code, dates, authority)
   - Authorization points (coordinates, volumes, flows)
   - Parameters (limits, units, frequencies)
3. **JSON Output**: Structured data ready for LeoWater DocTypes

## Troubleshooting

### Service won't start
- Check logs: `tail -100 /home/erpnext/.www/projects/app/docling/logs/docling.log`
- Verify permissions: `ls -la /home/erpnext/.www/projects/app/docling/logs/`
- Check port availability: `sudo lsof -i :7002`

### OCR not working
- Verify PaddleOCR service: `curl http://localhost:7001/health`
- Check PaddleOCR logs: `sudo supervisorctl tail -f paddleocr`

### Extraction errors
- Check Ollama service: `curl http://localhost:11434/api/tags`
- Verify model availability: `ollama list`
- Review extraction instructions in `/home/erpnext/.www/projects/app/docling/instructions.txt`

## Performance

- PDF text extraction: ~1-2 seconds per page
- OCR processing: ~3-5 seconds per page
- LLM extraction: ~10-30 seconds depending on model and document size

## Files

- `api.py` - Main FastAPI application
- `instructions.txt` - LLM extraction instructions
- `docling.conf` - Supervisor configuration
- `logs/` - Service logs
- `temp/` - Temporary file storage