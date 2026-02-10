# API Docling Setup Guide

FastAPI microservice for document conversion to Markdown using Docling v2.12.0 with GPU acceleration.

## Overview

- **Service**: api_docling
- **Port**: 6952
- **Virtual Environment**: `/home/pi/api_docling_env`
- **Directory**: `/home/pi/.services/api_docling`
- **Docling Version**: v2.12.0+ (with GPU accelerator support)

## Architecture

This service follows the standard FastAPI microservice architecture:

```
app/
├── main.py                 # FastAPI app with lifespan management
├── core/config.py          # Pydantic settings
├── middleware/             # Logging & error handling
├── api/v1/
│   ├── endpoints/          # Health, docling, transform UI
│   └── dependencies/       # Auth (optional)
├── services/               # Docling conversion logic
└── schemas/                # Pydantic models
```

## Installation Steps

### 1. Create Virtual Environment

```bash
cd /home/pi
python3 -m venv api_docling_env
source api_docling_env/bin/activate
```

### 2. Install Dependencies

```bash
cd /home/pi/.services/api_docling
pip install --upgrade pip
pip install -r requirements.txt
```

**Key Dependencies:**
- `docling>=2.12.0` - Document conversion library with GPU support
- `fastapi>=0.115.0` - Web framework
- `httpx>=0.27.0` - Async HTTP client
- `torch>=2.0.0` - GPU acceleration (CUDA)
- `easyocr>=1.7.0` - OCR engine
- `pypdfium2>=4.30.0` - PDF processing

### 3. Configuration

Create `.env` file (optional):

```bash
cat > /home/pi/.services/api_docling/.env << 'EOF'
# Docling Configuration
DOCLING_USE_GPU=true
DOCLING_DEVICE=cuda
DOCLING_DO_OCR=true
DOCLING_DO_TABLE_STRUCTURE=true
DOCLING_OCR_LANGUAGES=["en","es","fr","de"]

# External Services
PADDLEOCR_URL=http://localhost:6951/api/v1
OLLAMA_URL=http://localhost:11434

# Optional: API Authentication (empty list = disabled)
API_KEYS=[]

# Optional: Root path for nginx proxy
ROOT_PATH=
EOF
```

### 4. Verify GPU Support

```bash
source /home/pi/api_docling_env/bin/activate
python3 << 'EOF'
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
EOF
```

### 5. Setup Supervisor

```bash
# Copy supervisor config
sudo cp /home/pi/.services/api_docling/supervisor.conf /etc/supervisor/conf.d/api_docling.conf

# Reload and start
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start api_docling
```

### 6. Verify Installation

```bash
# Check status
sudo supervisorctl status api_docling

# Test health endpoint
curl http://localhost:6952/api/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "docling",
#   "version": "1.0.0",
#   "gpu_available": true,
#   "docling_initialized": true,
#   "external_services": {
#     "paddleocr": "available",
#     "ollama": "available"
#   }
# }
```

## Features

### 1. Document Conversion Endpoints

**POST /api/v1/convert**
- Convert document to Markdown (base64 input)
- Supports: PDF, DOCX, XLSX, PPTX, TXT, HTML, MD, RTF

**POST /api/v1/convert/file**
- Convert document via file upload
- Same format support as /convert

**POST /api/v1/convert-async**
- Async conversion for large documents
- Returns task_id for status tracking

**GET /api/v1/task/{task_id}**
- Check async conversion status
- Returns progress and results

**POST /api/v1/extract**
- Convert document + LLM extraction (Ollama)
- Structured data extraction from documents

### 2. Transform Web UI

**GET /api/v1/transform**
- Drag-and-drop file upload interface
- OCR settings panel
- Language selection
- Markdown preview & download
- Session history

Similar to:
- `/chat` in api_whisper (port 6950)
- `/forge` in api_paddleocr (port 6951)

### 3. Health Monitoring

**GET /api/v1/health**
- Service status
- GPU availability
- External service checks (PaddleOCR, Ollama)
- Docling initialization status

## Docling v2.12.0 Features

### GPU Acceleration (NEW in v2.12.0)

The service uses GPU accelerators for faster processing:

```python
from docling.datamodel.accelerator_options import AcceleratorOptions

pipeline_options = PdfPipelineOptions(
    accelerator_options=AcceleratorOptions(
        device="cuda",      # GPU device
        num_threads=4       # CPU threads
    ),
    do_ocr=True,
    do_table_structure=True
)
```

### OCR Support

- **Primary**: Docling built-in OCR with GPU
- **Fallback**: PaddleOCR API (port 6951) for scanned documents
- **Languages**: en, es, fr, de, it, pt, zh, ja, ko

### Table Detection

- Automatic table structure recognition
- Markdown table formatting
- Preserves table layouts from PDFs

## External Service Dependencies

### 1. PaddleOCR API (Required for OCR fallback)

- Port: 6951
- Endpoint: http://localhost:6951/api/v1/ocr
- Used when Docling detects scanned documents

### 2. Ollama (Optional - for LLM extraction)

- Port: 11434
- Used by /api/v1/extract endpoint
- Enables structured data extraction

## API Documentation

- **Swagger UI**: http://localhost:6952/api/v1/docs
- **ReDoc**: http://localhost:6952/api/v1/redoc
- **OpenAPI JSON**: http://localhost:6952/api/v1/openapi.json

## Directory Structure

```
/home/pi/.services/api_docling/
├── app/                    # Application code
├── static/                 # Web UI assets (CSS, JS)
├── logs/                   # Application logs
├── docling_temp/           # Temporary files
├── docling_uploads/        # Uploaded documents
├── docling_results/        # Conversion results
├── requirements.txt        # Python dependencies
├── supervisor.conf         # Supervisor configuration
└── .env                    # Environment variables (optional)
```

## Troubleshooting

### GPU Not Available

```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch CUDA support
source /home/pi/api_docling_env/bin/activate
python3 -c "import torch; print(torch.cuda.is_available())"

# If false, reinstall PyTorch with CUDA:
pip uninstall torch
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Service Won't Start

```bash
# Check logs
sudo tail -f /var/log/api_docling.err.log

# Test manually
source /home/pi/api_docling_env/bin/activate
cd /home/pi/.services/api_docling
uvicorn app.main:app --host 0.0.0.0 --port 6952
```

### PaddleOCR Not Available

```bash
# Check PaddleOCR service
curl http://localhost:6951/api/v1/health

# Start if needed
sudo supervisorctl start api_paddleocr
```

### Memory Issues

For large documents, adjust batch processing:

```bash
# In .env or config.py
DOCLING_BATCH_SIZE=1
DOCLING_MAX_PAGES=50
```

## Performance Tuning

### GPU Memory

- Service automatically uses CUDA if available
- GPU memory is cleaned up after each conversion
- Monitor with: `nvidia-smi -l 1`

### Worker Processes

Current: 2 workers (in supervisor.conf)

For high load:
```bash
# Edit supervisor.conf
command=/home/pi/api_docling_env/bin/uvicorn app.main:app --host 0.0.0.0 --port 6952 --workers 4
```

### Rate Limiting

Default: 20 requests/minute

Adjust in config.py:
```python
RATE_LIMIT_REQUESTS: int = 50
RATE_LIMIT_PERIOD: int = 60
```

## Nginx Proxy Configuration (Optional)

```nginx
location /docling {
    proxy_pass http://localhost:6952;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Important for file uploads
    client_max_body_size 100M;
}
```

Then set in .env:
```
ROOT_PATH=/docling
```

## Migration from Legacy api.py

The original `api.py` has been refactored into the standard architecture:

| Old | New |
|-----|-----|
| GET / | GET / |
| GET /health | GET /api/v1/health |
| POST /convert | POST /api/v1/convert |
| POST /convert-async | POST /api/v1/convert-async |
| GET /task/{id} | GET /api/v1/task/{id} |
| POST /extract | POST /api/v1/extract |
| - | GET /api/v1/transform (NEW) |

All functionality is preserved with enhanced:
- Error handling
- Request logging
- GPU monitoring
- Service health checks

## Support

For issues:
1. Check logs: `/var/log/api_docling.err.log`
2. Verify GPU: `nvidia-smi`
3. Test health: `curl http://localhost:6952/api/v1/health`
4. Review Docling docs: https://github.com/docling-project/docling
