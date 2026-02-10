#!/usr/bin/env python3
"""
Transform web interface for document conversion.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from logzero import logger

from app.core.config import settings

router = APIRouter()


@router.get("/transform", response_class=HTMLResponse, tags=["Web Interface"])
async def transform_interface(request: Request):
    """
    Serve Transform web interface for document conversion.
    """
    # Use ROOT_PATH from settings for proxy compatibility
    base_path = settings.ROOT_PATH
    api_endpoint = f"{base_path}{settings.API_V1_STR}/convert/file"

    logger.info(f"Serving Transform interface - base_path: '{base_path}', ROOT_PATH: '{settings.ROOT_PATH}'")

    html_content = f"""
<!DOCTYPE html>
<html lang="en" id="html-root">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#3b82f6">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Transform">
    <meta name="description" content="Convert documents to Markdown with AI-powered conversion">
    <title>Document Transform</title>

    <link rel="stylesheet" href="{base_path}/static/css/bootstrap.min.css?v=11">
    <link rel="stylesheet" href="{base_path}/static/css/bootstrap-icons.min.css?v=11">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&family=Raleway:wght@300;400;500;600;700&display=swap">
    <link rel="stylesheet" href="{base_path}/static/css/transform.css?v=11">
</head>
<body>
    <div class="app-container" id="appContainer">
        <!-- Mobile Overlay -->
        <div class="mobile-overlay" id="mobileOverlay" onclick="closeSidebar()"></div>

        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <button class="sidebar-toggle" onclick="toggleSidebar()">
                    <i class="bi bi-chevron-right" id="sidebarIcon"></i>
                </button>
                <div class="sidebar-title">Transform</div>
            </div>
            <button class="new-session-btn btn btn-outline-light" onclick="newSession()">
                <i class="bi bi-plus-circle"></i> New Session
            </button>
            <div class="search-box">
                <span>🔍</span>
                <input type="text" placeholder="Search sessions..." id="searchInput" oninput="filterSessions()">
            </div>
            <div class="sessions-list" id="sessionsList"></div>
            <div class="sidebar-footer">
                <button class="sidebar-user-btn" onclick="openSettings()">
                    <span class="user-avatar">T</span>
                    <div class="user-info">
                        <div class="user-name">Transform User</div>
                    </div>
                    <span class="settings-icon">⚙️</span>
                </button>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="top-bar">
                <button class="sidebar-toggle" onclick="toggleSidebar()">
                    <i class="bi bi-chevron-right" id="topbarIcon"></i>
                </button>
            </div>
            <div class="conversion-area" id="conversionArea">
                <div class="welcome-message">
                    <h1><i class="bi bi-file-earmark-text"></i> Document Transform</h1>
                    <p>Upload PDF, DOCX, XLSX, or PPTX files to convert to Markdown</p>
                </div>
            </div>
            <div class="controls">
                <div class="processing-status" id="processingStatus">
                    <div class="processing-spinner"></div>
                    <span>Converting</span>
                    <span class="processing-info" id="processingInfo"></span>
                </div>
                <div class="upload-area" id="uploadArea">
                    <input type="file" id="fileInput" accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.html,.md,.rtf" onchange="handleFileSelect(event)">
                    <label for="fileInput" class="upload-label">
                        <i class="bi bi-cloud-upload"></i>
                        <span>Choose file or drag here</span>
                        <small>Supports: PDF, DOCX, XLSX, PPTX, TXT, HTML, RTF</small>
                    </label>
                </div>
                <div class="controls-buttons">
                    <button class="control-btn btn btn-primary" onclick="document.getElementById('fileInput').click()" title="Upload File">
                        <i class="bi bi-upload"></i>
                    </button>
                    <button class="control-btn btn btn-warning" onclick="openExtractModal()" title="Extract with LLM">
                        <i class="bi bi-cpu"></i>
                    </button>
                    <button class="control-btn btn btn-success" onclick="downloadMarkdown()" title="Download Markdown">
                        <i class="bi bi-download"></i>
                    </button>
                    <button class="control-btn btn btn-info" onclick="copyMarkdown()" title="Copy to Clipboard">
                        <i class="bi bi-clipboard"></i>
                    </button>
                    <button class="control-btn btn btn-secondary" onclick="clearSession()" title="Clear Session">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Settings Modal -->
    <div class="modal-overlay" id="settingsModal" onclick="closeModalOnOverlay(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <button class="modal-close" onclick="closeSettings()">×</button>
            <div class="modal-layout">
                <div class="modal-sidebar">
                    <button class="modal-section-btn active" onclick="showSettingsSection('general')">
                        ⚙️ General
                    </button>
                    <button class="modal-section-btn" onclick="showSettingsSection('advanced')">
                        🔧 Advanced
                    </button>
                </div>
                <div class="modal-main">
                    <div class="settings-section active" id="generalSettings">
                        <h2 class="modal-title">General Settings</h2>
                        <div class="setting-group">
                            <label>API Key</label>
                            <input type="password" id="apiKeyInput" placeholder="Enter your API Key">
                        </div>
                    </div>
                    <div class="settings-section" id="advancedSettings">
                        <h2 class="modal-title">Conversion Settings</h2>
                        <div class="setting-group">
                            <label>
                                <input type="checkbox" id="useOcrCheck" checked>
                                Use OCR for scanned documents
                            </label>
                        </div>
                        <div class="setting-group">
                            <label>
                                <input type="checkbox" id="detectTablesCheck" checked>
                                Detect and format tables
                            </label>
                        </div>
                        <div class="setting-group">
                            <label>OCR Language</label>
                            <select id="ocrLanguageSelect">
                                <option value="en" selected>English</option>
                                <option value="es">Spanish</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="it">Italian</option>
                                <option value="pt">Portuguese</option>
                                <option value="zh">Chinese</option>
                                <option value="ja">Japanese</option>
                                <option value="ko">Korean</option>
                            </select>
                        </div>
                        <button class="save-settings-btn btn btn-primary" onclick="saveSettings()">
                            <i class="bi bi-check-circle"></i> Save Settings
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Extract Modal -->
    <div class="modal fade" id="extractModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Extract with LLM</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label for="llmModelSelect" class="form-label">Model</label>
                        <select class="form-select" id="llmModelSelect">
                            <option value="qwen2.5:7b" selected>Qwen 2.5 7B</option>
                            <option value="mistral:7b">Mistral 7B</option>
                            <option value="llama3.2:3b">Llama 3.2 3B</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="extractInstructions" class="form-label">Instructions</label>
                        <textarea class="form-control" id="extractInstructions" rows="8" placeholder="Enter extraction instructions...">Extract authorization data and return ONLY valid JSON with this structure:
{{
  "lw_dossier": {{}},
  "lw_authorization_points": [...],
  "lw_parameters": [...]
}}</textarea>
                    </div>
                    <div class="alert alert-info mb-0">
                        <i class="bi bi-info-circle"></i> The already-converted markdown will be sent to the LLM for extraction.
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-warning" onclick="performExtraction()">
                        <i class="bi bi-cpu"></i> Extract
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Confirm Modal -->
    <div class="modal fade" id="confirmModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="confirmModalTitle">Confirm Action</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" id="confirmModalBody">
                    Are you sure?
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirmModalButton">Confirm</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notification -->
    <div class="toast-notification" id="toastNotification">
        <i class="bi bi-check-circle"></i>
        <span id="toastMessage">Success!</span>
    </div>

    <script src="{base_path}/static/js/bootstrap.bundle.min.js?v=11"></script>
    <script>
        // API configuration injected from server
        window.API_ENDPOINT = '{api_endpoint}';
        window.BASE_PATH = '{base_path}';
    </script>
    <script src="{base_path}/static/js/transform.js?v=11"></script>
    <script>
        // Initialize when DOM is ready
        if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", init);
        }} else {{
            init();
        }}
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)
