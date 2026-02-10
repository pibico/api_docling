#!/usr/bin/env python3
"""
Document Transform web interface following pibiCo guidelines.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from logzero import logger

from app.core.config import settings

router = APIRouter()


@router.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def web_interface(request: Request):
    """
    Serve pibiCo-branded Document Transform web interface at root path.
    """
    # Use ROOT_PATH from settings for proxy compatibility
    base_path = settings.ROOT_PATH if settings.ROOT_PATH else ''
    api_endpoint = f"{base_path}{settings.API_V1_STR}/convert/file"
    api_extract = f"{base_path}{settings.API_V1_STR}/extract-markdown"
    api_docs = f"{base_path}{settings.API_V1_STR}/docs"
    api_redoc = f"{base_path}{settings.API_V1_STR}/redoc"

    logger.info(f"Serving web interface - base: {base_path}")

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#4682B4">
    <meta name="description" content="AI-powered document conversion service by pibiCo">
    <title>Document Transform - pibiCo AI Services</title>

    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="{base_path}/static/pibico_icon.svg">

    <!-- Styles -->
    <link rel="stylesheet" href="{base_path}/static/css/bootstrap.min.css">
    <link rel="stylesheet" href="{base_path}/static/css/bootstrap-icons.min.css">
    <link rel="stylesheet" href="{base_path}/static/css/pibico.css">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            background: linear-gradient(135deg, #2c5171 0%, #4682b4 50%, #6a9bc3 100%);
            min-height: 100vh;
            color: #1A1A2E;
        }}

        /* Navbar Card */
        .navbar {{
            position: fixed;
            top: 8px;
            left: 12px;
            right: 12px;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.6rem 1.5rem;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            background: rgba(255, 255, 255, 0.85);
            border-radius: 12px;
            box-shadow: 0 0 12px rgba(70, 130, 180, 0.15),
                        0 0 4px rgba(70, 130, 180, 0.08);
            line-height: 1.1;
        }}

        .navbar-title {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #4682B4 0%, #B33A2B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .navbar-nav {{
            display: flex;
            flex-direction: row;
            gap: 0.5rem;
            align-items: center;
            list-style: none;
            margin: 0;
            padding: 0;
        }}

        .navbar-nav li {{
            display: inline-block;
            margin: 0;
            padding: 0;
        }}

        .nav-link {{
            color: #4682B4;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.8rem;
            padding: 0.35rem 0.75rem;
            border-radius: 8px;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}

        .nav-link:hover {{
            background: #D6E8F5;
            color: #365F8A;
        }}

        .nav-link svg {{
            flex-shrink: 0;
        }}

        .btn-icon {{
            width: 34px;
            height: 34px;
            border: none;
            border-radius: 8px;
            background: #E8E8EA;
            color: #4682B4;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}

        .btn-icon:hover {{
            background: #D6E8F5;
            color: #365F8A;
        }}

        /* Main Content */
        .app-main {{
            margin-top: 60px;
            margin-bottom: 44px;
            padding: 12px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }}

        /* Floating Action Bar */
        .action-bar {{
            position: fixed;
            left: 12px;
            top: calc(50% - 80px);
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 8px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            background: rgba(255, 255, 255, 0.85);
            border-radius: 12px;
            box-shadow: 0 0 12px rgba(70, 130, 180, 0.15),
                        0 0 4px rgba(70, 130, 180, 0.08);
            padding: 8px;
        }}

        .action-btn {{
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }}

        .action-btn-convert {{
            background: #B33A2B;
            color: #FFFFFF;
            box-shadow: 0 2px 8px rgba(179, 58, 43, 0.3);
        }}

        .action-btn-convert:hover {{
            background: #8A2A1F;
            transform: translateY(-1px);
        }}

        .action-btn-convert:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}

        .action-btn-download {{
            background: #4682B4;
            color: #FFFFFF;
            box-shadow: 0 2px 8px rgba(70, 130, 180, 0.3);
        }}

        .action-btn-download:hover {{
            background: #365F8A;
            transform: translateY(-1px);
        }}

        .action-btn-download:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }}

        .action-btn-clear {{
            background: #E8E8EA;
            color: #6E6E76;
        }}

        .action-btn-clear:hover {{
            background: #D6E8F5;
            color: #365F8A;
        }}

        /* Cards */
        .pibico-card {{
            background: #FFFFFF;
            border: none;
            border-radius: 12px;
            padding: 24px;
            line-height: 1.2;
            box-shadow: 0 0 12px rgba(70, 130, 180, 0.15),
                        0 0 4px rgba(70, 130, 180, 0.08);
            transition: box-shadow 0.2s ease;
            margin-bottom: 20px;
        }}

        .pibico-card:hover {{
            box-shadow: 0 0 20px rgba(70, 130, 180, 0.25),
                        0 0 8px rgba(70, 130, 180, 0.12);
        }}

        .card-title {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            font-size: 1.4rem;
            font-weight: 600;
            color: #1A1A2E;
            margin-bottom: 12px;
        }}

        .upload-area {{
            border: 2px dashed #4682B4;
            border-radius: 12px;
            padding: 40px;
            text-align: center;
            background: rgba(70, 130, 180, 0.05);
            cursor: pointer;
            transition: all 0.3s;
        }}

        .upload-area:hover {{
            background: rgba(70, 130, 180, 0.1);
            border-color: #365F8A;
        }}

        .upload-area.has-file {{
            background: rgba(70, 130, 180, 0.1);
            border-color: #4682B4;
            border-style: solid;
        }}

        .upload-area input[type="file"] {{
            display: none;
        }}

        .result-container {{
            margin-top: 20px;
            display: none;
        }}

        .result-container.show {{
            display: block;
        }}

        .markdown-content {{
            padding: 16px;
            background: #F8F9FA;
            border-radius: 8px;
            max-height: 500px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(70, 130, 180, 0.3);
            border-radius: 50%;
            border-top-color: #4682B4;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}

        /* Toast Notifications */
        .toast-container {{
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 400px;
        }}

        .toast {{
            background: #FFFFFF;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease;
            border-left: 4px solid #4682B4;
        }}

        .toast.success {{ border-left-color: #28a745; }}
        .toast.error {{ border-left-color: #B33A2B; }}
        .toast.warning {{ border-left-color: #FFC107; }}
        .toast.info {{ border-left-color: #4682B4; }}

        .toast-icon {{ font-size: 1.5rem; flex-shrink: 0; }}
        .toast.success .toast-icon {{ color: #28a745; }}
        .toast.error .toast-icon {{ color: #B33A2B; }}
        .toast.warning .toast-icon {{ color: #FFC107; }}
        .toast.info .toast-icon {{ color: #4682B4; }}

        .toast-content {{
            flex: 1;
            font-size: 0.9rem;
            color: #1A1A2E;
        }}

        .toast-close {{
            background: none;
            border: none;
            color: #6E6E76;
            cursor: pointer;
            font-size: 1.2rem;
            padding: 0;
            line-height: 1;
        }}

        .toast-close:hover {{ color: #1A1A2E; }}

        @keyframes slideIn {{
            from {{ transform: translateX(400px); opacity: 0; }}
            to {{ transform: translateX(0); opacity: 1; }}
        }}

        @keyframes slideOut {{
            from {{ transform: translateX(0); opacity: 1; }}
            to {{ transform: translateX(400px); opacity: 0; }}
        }}

        /* Footer Card */
        .app-footer {{
            position: fixed;
            bottom: 8px;
            left: 12px;
            right: 12px;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.4rem 1.5rem;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            background: rgba(255, 255, 255, 0.85);
            border-radius: 12px;
            box-shadow: 0 0 12px rgba(70, 130, 180, 0.15),
                        0 0 4px rgba(70, 130, 180, 0.08);
            font-size: 0.75rem;
            color: #6E6E76;
        }}

        .footer-separator {{ color: #C8C8CC; }}
        .footer-link {{
            color: #4682B4;
            text-decoration: none;
        }}
        .footer-link:hover {{ text-decoration: underline; }}

        /* Slide Panel */
        .pibico-panel-backdrop {{
            position: fixed;
            inset: 0;
            background: rgba(26, 26, 46, 0.4);
            z-index: 999;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }}

        .pibico-panel-backdrop.active {{
            opacity: 1;
            visibility: visible;
        }}

        .pibico-panel {{
            position: fixed;
            top: 0;
            right: 0;
            width: 45%;
            height: 100vh;
            background: #FFFFFF;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow-y: auto;
            box-shadow: -4px 0 24px rgba(26, 26, 46, 0.15);
        }}

        .pibico-panel.active {{
            transform: translateX(0);
        }}

        .pibico-panel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: linear-gradient(135deg, #4682B4 0%, #365F8A 100%);
            color: #FFFFFF;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 1;
        }}

        .pibico-panel-close {{
            background: none;
            border: none;
            color: #FFFFFF;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 6px;
            line-height: 1;
        }}

        .pibico-panel-close:hover {{
            background: rgba(255, 255, 255, 0.15);
        }}

        .pibico-panel-body {{
            padding: 20px;
        }}

        .pibico-input {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            font-size: 0.9rem;
            padding: 10px 12px;
            border: none;
            border-radius: 8px;
            background: #E8E8EA;
            color: #1A1A2E;
            width: 100%;
            outline: none;
            transition: box-shadow 0.2s ease;
        }}

        .pibico-input:focus {{
            box-shadow: 0 0 0 2px #4682B4;
            background: #FFFFFF;
        }}

        .pibico-textarea {{
            font-family: monospace;
            font-size: 0.85rem;
            padding: 10px 12px;
            border: none;
            border-radius: 8px;
            background: #E8E8EA;
            color: #1A1A2E;
            width: 100%;
            min-height: 200px;
            outline: none;
            transition: box-shadow 0.2s ease;
            resize: vertical;
        }}

        .pibico-textarea:focus {{
            box-shadow: 0 0 0 2px #4682B4;
            background: #FFFFFF;
        }}

        .form-group {{
            margin-bottom: 16px;
        }}

        .form-label {{
            display: block;
            font-weight: 500;
            margin-bottom: 6px;
            color: #1A1A2E;
        }}

        .pibico-btn {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', Arial, sans-serif;
            font-weight: 500;
            font-size: 0.85rem;
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            line-height: 1.1;
        }}

        .pibico-btn-primary {{
            background: #4682B4;
            color: #FFFFFF;
        }}

        .pibico-btn-primary:hover {{
            background: #365F8A;
        }}

        .pibico-btn-warning {{
            background: #FFA500;
            color: #FFFFFF;
        }}

        .pibico-btn-warning:hover {{
            background: #CC8400;
        }}

        @media (max-width: 768px) {{
            .pibico-panel {{ width: 100%; }}
            .navbar {{
                left: 6px;
                right: 6px;
                top: 6px;
                padding: 3px 12px;
            }}
            .navbar-title {{ font-size: 1.2rem; }}
            .app-footer {{
                left: 6px;
                right: 6px;
                bottom: 6px;
                padding: 3px 12px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span class="navbar-title">Document Transform</span>
        </div>
        <ul class="navbar-nav">
            <li><button class="btn-icon" onclick="openSettings()" title="Settings"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></button></li>
            <li><a href="{api_docs}" class="nav-link" target="_blank" title="API Docs"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg> API</a></li>
        </ul>
    </nav>

    <!-- Main Content -->
    <main class="app-main">
        <div class="pibico-card">
            <h2 class="card-title">
                <i class="bi bi-file-earmark-text"></i> Document Conversion
            </h2>
            <p style="margin-bottom: 20px; color: #6E6E76;">
                Upload PDF, DOCX, XLSX, or PPTX files to convert to Markdown
            </p>

            <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                <input type="file" id="fileInput" accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.ppt,.txt,.html,.md,.rtf" onchange="handleFileSelect(event)">
                <div id="uploadPrompt">
                    <i class="bi bi-cloud-upload" style="font-size: 3rem; color: #4682B4;"></i>
                    <p style="margin-top: 12px; font-size: 1.1rem; color: #1A1A2E;">
                        Click to upload or drag & drop
                    </p>
                    <p style="color: #6E6E76; font-size: 0.85rem;">
                        Supports: PDF, DOCX, XLSX, PPTX, TXT, HTML, RTF
                    </p>
                </div>
                <div id="fileInfo" style="display: none; text-align: center;">
                    <i class="bi bi-file-earmark-check" style="font-size: 2.5rem; color: #4682B4;"></i>
                    <p style="margin-top: 8px; font-weight: 600; color: #1A1A2E;">
                        <span id="fileNameText"></span>
                    </p>
                    <p style="color: #6E6E76; font-size: 0.85rem;">
                        <span id="fileSizeText"></span>
                    </p>
                </div>
            </div>

            <div id="resultContainer" class="result-container">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h3 style="margin: 0;">Converted Markdown</h3>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn-icon" onclick="copyMarkdown()" title="Copy to clipboard">
                            <i class="bi bi-clipboard"></i>
                        </button>
                        <button class="btn-icon" onclick="downloadMarkdown()" title="Download as .md">
                            <i class="bi bi-download"></i>
                        </button>
                    </div>
                </div>
                <div id="markdownContent" class="markdown-content"></div>
            </div>
        </div>
    </main>

    <!-- Floating Action Bar -->
    <div class="action-bar">
        <button class="action-btn action-btn-convert" id="convertBtn" onclick="convertDocument()" title="Convert Document" disabled>
            <i class="bi bi-arrow-repeat"></i>
        </button>
        <button class="action-btn action-btn-download" id="downloadBtn" onclick="downloadMarkdown()" title="Download Markdown" disabled>
            <i class="bi bi-download"></i>
        </button>
        <button class="action-btn action-btn-clear" onclick="clearAll()" title="Clear">
            <i class="bi bi-trash"></i>
        </button>
    </div>

    <!-- Toast Container -->
    <div class="toast-container" id="toastContainer"></div>

    <!-- Footer -->
    <footer class="app-footer">
        <span><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M15 9.354a4 4 0 1 0 0 5.292" stroke-linecap="round"/></svg> pibiCo 2026</span>
        <span class="footer-separator">|</span>
        <a href="{api_redoc}" target="_blank" class="footer-link"><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg> ReDoc</a>
        <span class="footer-separator">|</span>
        <span><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg> v{settings.VERSION}</span>
    </footer>

    <!-- Settings Panel -->
    <div class="pibico-panel-backdrop" id="settingsBackdrop" onclick="closeSettings()"></div>
    <div class="pibico-panel" id="settingsPanel">
        <div class="pibico-panel-header">
            <span><i class="bi bi-gear"></i> Settings</span>
            <button class="pibico-panel-close" onclick="closeSettings()">&times;</button>
        </div>
        <div class="pibico-panel-body">
            <h3 style="margin-bottom: 16px; font-weight: 600;">Authentication</h3>
            <div class="form-group">
                <label class="form-label">API Key</label>
                <input type="password" id="settingsApiKey" class="pibico-input" placeholder="Enter your API Key">
            </div>

            <h3 style="margin: 24px 0 16px 0; font-weight: 600;">Conversion Options</h3>
            <div class="form-group">
                <label class="form-label">
                    <input type="checkbox" id="useOcrCheck" checked> Use OCR for scanned documents
                </label>
            </div>
            <div class="form-group">
                <label class="form-label">
                    <input type="checkbox" id="detectTablesCheck" checked> Detect and format tables
                </label>
            </div>
            <div class="form-group">
                <label class="form-label">OCR Language</label>
                <select id="ocrLanguageSelect" class="pibico-input">
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

            <button class="pibico-btn pibico-btn-primary" onclick="saveSettings()">
                <i class="bi bi-check-circle"></i> Save Settings
            </button>
        </div>
    </div>

    <script>
        const API_ENDPOINT = '{api_endpoint}';
        const API_EXTRACT = '{api_extract}';
        const BASE_PATH = '{base_path}';

        let selectedFile = null;
        let apiKey = sessionStorage.getItem('docling_api_key') || '';
        let currentMarkdown = null;
        let currentFilename = null;

        // Toast notification system
        function showToast(message, type = 'info', duration = 4000) {{
            const container = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = 'toast ' + type;

            const icons = {{
                success: '<i class="bi bi-check-circle-fill"></i>',
                error: '<i class="bi bi-x-circle-fill"></i>',
                warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
                info: '<i class="bi bi-info-circle-fill"></i>'
            }};

            const iconDiv = document.createElement('div');
            iconDiv.className = 'toast-icon';
            iconDiv.innerHTML = icons[type] || icons.info;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'toast-content';
            contentDiv.textContent = message;

            const closeBtn = document.createElement('button');
            closeBtn.className = 'toast-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.onclick = function() {{ this.parentElement.remove(); }};

            toast.appendChild(iconDiv);
            toast.appendChild(contentDiv);
            toast.appendChild(closeBtn);
            container.appendChild(toast);

            setTimeout(() => {{
                toast.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }}, duration);
        }}

        function handleFileSelect(event) {{
            selectedFile = event.target.files[0];
            if (selectedFile) {{
                document.getElementById('convertBtn').disabled = false;

                const uploadArea = document.getElementById('uploadArea');
                uploadArea.classList.add('has-file');
                document.getElementById('uploadPrompt').style.display = 'none';
                document.getElementById('fileInfo').style.display = 'block';

                document.getElementById('fileNameText').textContent = selectedFile.name;
                const fileSizeMB = (selectedFile.size / 1024 / 1024).toFixed(2);
                document.getElementById('fileSizeText').textContent = fileSizeMB + ' MB';
            }}
        }}

        function clearAll() {{
            selectedFile = null;
            currentMarkdown = null;
            currentFilename = null;
            document.getElementById('fileInput').value = '';
            document.getElementById('convertBtn').disabled = true;
            document.getElementById('downloadBtn').disabled = true;
            document.getElementById('resultContainer').classList.remove('show');

            const uploadArea = document.getElementById('uploadArea');
            uploadArea.classList.remove('has-file');
            document.getElementById('uploadPrompt').style.display = 'block';
            document.getElementById('fileInfo').style.display = 'none';
        }}

        async function convertDocument() {{
            if (!apiKey) {{
                showToast('Please configure your API key in Settings first', 'warning');
                openSettings();
                return;
            }}

            if (!selectedFile) {{
                showToast('Please select a file first', 'warning');
                return;
            }}

            const btn = document.getElementById('convertBtn');
            const originalHTML = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>';

            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('use_ocr', document.getElementById('useOcrCheck').checked);
            formData.append('detect_tables', document.getElementById('detectTablesCheck').checked);
            formData.append('ocr_language', document.getElementById('ocrLanguageSelect').value);

            try {{
                const response = await fetch(API_ENDPOINT, {{
                    method: 'POST',
                    headers: {{
                        'X-API-Key': apiKey
                    }},
                    body: formData
                }});

                if (response.ok) {{
                    const result = await response.json();
                    currentMarkdown = result.markdown;
                    currentFilename = selectedFile.name;
                    displayResults(result);
                    document.getElementById('downloadBtn').disabled = false;
                    showToast('Document converted successfully!', 'success');
                }} else {{
                    const error = await response.json();
                    showToast('Error: ' + (error.detail || 'Conversion failed'), 'error');
                }}
            }} catch (error) {{
                showToast('Error: ' + error.message, 'error');
            }} finally {{
                btn.innerHTML = originalHTML;
                if (selectedFile) {{
                    btn.disabled = false;
                }}
            }}
        }}

        function displayResults(result) {{
            const container = document.getElementById('resultContainer');
            const content = document.getElementById('markdownContent');

            content.textContent = result.markdown;
            container.classList.add('show');
        }}

        function copyMarkdown() {{
            if (!currentMarkdown) {{
                showToast('No markdown to copy', 'warning');
                return;
            }}

            navigator.clipboard.writeText(currentMarkdown).then(() => {{
                showToast('Markdown copied to clipboard!', 'success');
            }}).catch(() => {{
                showToast('Failed to copy to clipboard', 'error');
            }});
        }}

        function downloadMarkdown() {{
            if (!currentMarkdown) {{
                showToast('No markdown to download', 'warning');
                return;
            }}

            const blob = new Blob([currentMarkdown], {{ type: 'text/markdown;charset=utf-8' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const originalName = currentFilename.replace(/\\.[^/.]+$/, '');
            a.download = originalName + '.md';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showToast('Markdown downloaded successfully!', 'success');
        }}

        function openSettings() {{
            document.getElementById('settingsPanel').classList.add('active');
            document.getElementById('settingsBackdrop').classList.add('active');
            document.getElementById('settingsApiKey').value = apiKey;
        }}

        function closeSettings() {{
            document.getElementById('settingsPanel').classList.remove('active');
            document.getElementById('settingsBackdrop').classList.remove('active');
        }}

        function saveSettings() {{
            apiKey = document.getElementById('settingsApiKey').value.trim();
            if (apiKey) {{
                sessionStorage.setItem('docling_api_key', apiKey);
                closeSettings();
                showToast('Settings saved successfully!', 'success');
            }} else {{
                showToast('Please enter an API key', 'warning');
            }}
        }}

        // Close panels on Escape key
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                closeSettings();
            }}
        }});

        // Drag and drop support
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('dragover', (e) => {{
            e.preventDefault();
            uploadArea.style.borderColor = '#365F8A';
            uploadArea.style.background = 'rgba(70, 130, 180, 0.15)';
        }});

        uploadArea.addEventListener('dragleave', () => {{
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';
        }});

        uploadArea.addEventListener('drop', (e) => {{
            e.preventDefault();
            uploadArea.style.borderColor = '';
            uploadArea.style.background = '';

            const files = e.dataTransfer.files;
            if (files.length > 0) {{
                document.getElementById('fileInput').files = files;
                handleFileSelect({{ target: {{ files: files }} }});
            }}
        }});
    </script>
</body>
</html>
    """

    return HTMLResponse(content=html_content)
