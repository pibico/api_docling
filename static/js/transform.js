// Document Transform - Web interface for Docling API
const API_ENDPOINT = window.API_ENDPOINT || '/api/v1/convert/file';
const BASE_PATH = window.BASE_PATH || '';

// Storage keys
const STORAGE_PREFIX = 'doc_transform_';
const SESSIONS_KEY = STORAGE_PREFIX + 'sessions';
const CURRENT_SESSION_KEY = STORAGE_PREFIX + 'current_session';
const SETTINGS_KEY = STORAGE_PREFIX + 'settings';

// Global state
let currentSession = null;
let sessions = [];
let settings = {
    apiKey: '',
    useOcr: true,
    detectTables: true,
    ocrLanguage: 'en'
};

let currentMarkdown = '';
let currentFilename = '';

// Initialize application
function init() {
    console.log('Transform UI initializing...');

    try {
        loadSettings();
        loadSessions();
        setupEventListeners();
        setupDragAndDrop();

        // Fix mobile viewport height
        function setVH() {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
        }
        setVH();
        window.addEventListener('resize', setVH);
        window.addEventListener('orientationchange', () => {
            setTimeout(setVH, 100);
        });

        // Ensure sidebar starts collapsed on desktop, expanded on mobile
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            if (window.innerWidth > 768) {
                // Desktop: start collapsed
                sidebar.classList.add('collapsed');
            } else {
                // Mobile: start collapsed
                sidebar.classList.add('collapsed');
            }
            console.log('Sidebar initialized:', sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded');
        } else {
            console.error('Sidebar element not found!');
        }

        // Create initial session if none exists
        if (!currentSession) {
            newSession();
        }

        console.log('Transform UI initialized successfully');
    } catch (error) {
        console.error('Error initializing Transform UI:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
}

// Setup drag and drop
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('drag-over');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('drag-over');
        }, false);
    });

    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    }, false);
}

// Handle file selection
function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length > 0) {
        handleFiles(files);
    }
}

// Handle files
async function handleFiles(files) {
    const file = files[0]; // Process one file at a time

    // Validate file type
    const validExtensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.html', '.md', '.rtf'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExt)) {
        showToast('Invalid file type. Please upload a document file.', 'error');
        return;
    }

    currentFilename = file.name;
    await convertDocument(file);
}

// Convert document
async function convertDocument(file) {
    const processingStatus = document.getElementById('processingStatus');
    const processingInfo = document.getElementById('processingInfo');
    const conversionArea = document.getElementById('conversionArea');

    try {
        // Show processing status
        if (processingStatus) {
            processingStatus.classList.add('active');
            processingInfo.textContent = file.name;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('use_ocr', settings.useOcr);
        formData.append('detect_tables', settings.detectTables);

        // Send request
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData,
            headers: settings.apiKey ? {
                'X-API-Key': settings.apiKey
            } : {}
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Conversion failed');
        }

        const result = await response.json();
        currentMarkdown = result.markdown || '';

        // Display result
        displayMarkdown(currentMarkdown, file.name);

        // Update session
        if (currentSession) {
            currentSession.results.push({
                filename: file.name,
                markdown: currentMarkdown,
                timestamp: new Date().toISOString(),
                pages: result.pages,
                tables_detected: result.tables_detected,
                ocr_used: result.ocr_used
            });
            saveSession(currentSession);
            updateSessionsList();
        }

        showToast(`Successfully converted ${file.name}`);

    } catch (error) {
        console.error('Conversion error:', error);
        showToast(`Error: ${error.message}`, 'error');

        if (conversionArea) {
            conversionArea.innerHTML = `
                <div class="error-message">
                    <i class="bi bi-exclamation-triangle"></i>
                    <h3>Conversion Failed</h3>
                    <p>${error.message}</p>
                </div>
            `;
        }
    } finally {
        if (processingStatus) {
            processingStatus.classList.remove('active');
        }
    }
}

// Display markdown
function displayMarkdown(markdown, filename) {
    const conversionArea = document.getElementById('conversionArea');
    if (!conversionArea) return;

    // Create markdown preview
    const preview = document.createElement('div');
    preview.className = 'result-card';
    preview.innerHTML = `
        <div class="result-header">
            <div class="result-info">
                <i class="bi bi-file-earmark-text"></i>
                <div>
                    <div class="result-filename">${filename}</div>
                    <div class="result-meta">${markdown.length} characters</div>
                </div>
            </div>
        </div>
        <div class="result-content">
            <div class="markdown-preview">
                <pre><code>${escapeHtml(markdown)}</code></pre>
            </div>
        </div>
    `;

    conversionArea.innerHTML = '';
    conversionArea.appendChild(preview);
}

// Download markdown
function downloadMarkdown() {
    if (!currentMarkdown) {
        showToast('No markdown to download', 'error');
        return;
    }

    const blob = new Blob([currentMarkdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFilename.replace(/\.[^/.]+$/, '') + '.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Markdown downloaded!');
}

// Copy markdown to clipboard
async function copyMarkdown() {
    if (!currentMarkdown) {
        showToast('No markdown to copy', 'error');
        return;
    }

    try {
        await navigator.clipboard.writeText(currentMarkdown);
        showToast('Markdown copied to clipboard!');
    } catch (error) {
        showToast('Failed to copy to clipboard', 'error');
    }
}

// Open extract modal
function openExtractModal() {
    if (!currentMarkdown) {
        showToast('Please convert a document first', 'error');
        return;
    }

    const modal = document.getElementById('extractModal');
    new bootstrap.Modal(modal).show();
}

// Perform extraction with LLM
async function performExtraction() {
    if (!currentMarkdown) {
        showToast('Please convert a document first', 'error');
        return;
    }

    const modal = bootstrap.Modal.getInstance(document.getElementById('extractModal'));
    const model = document.getElementById('llmModelSelect').value;
    const instructions = document.getElementById('extractInstructions').value;

    try {
        // Close modal
        modal.hide();

        // Show processing status
        const processingStatus = document.getElementById('processingStatus');
        const processingInfo = document.getElementById('processingInfo');
        if (processingStatus) {
            processingStatus.classList.add('active');
            processingInfo.textContent = 'Extracting with ' + model + '...';
        }

        // Send markdown directly to extraction endpoint
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 310000); // 310 seconds (slightly more than backend)

        try {
            const response = await fetch(window.BASE_PATH + '/api/v1/extract-markdown', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(settings.apiKey ? { 'X-API-Key': settings.apiKey } : {})
                },
                body: JSON.stringify({
                    markdown: currentMarkdown,
                    model: model,
                    instructions: instructions
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Extraction failed');
            }

            const result = await response.json();

            // Display extraction result
            displayExtractionResult(result);

            showToast('Extraction completed successfully!');

        } catch (fetchError) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error('Extraction timed out. The document may be too large.');
            }
            throw fetchError;
        }

    } catch (error) {
        console.error('Extraction error:', error);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        const processingStatus = document.getElementById('processingStatus');
        if (processingStatus) {
            processingStatus.classList.remove('active');
        }
    }
}

// Display extraction result
function displayExtractionResult(result) {
    const conversionArea = document.getElementById('conversionArea');
    if (!conversionArea) return;

    let extractionHTML = '';

    if (result.status === 'success' && result.extraction) {
        // Pretty print JSON
        const jsonStr = JSON.stringify(result.extraction, null, 2);
        extractionHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div class="result-info">
                        <i class="bi bi-cpu"></i>
                        <div>
                            <div class="result-filename">LLM Extraction Result</div>
                            <div class="result-meta">Model: ${result.model} | Markdown: ${result.markdown_length} chars</div>
                        </div>
                    </div>
                    <button class="btn btn-sm btn-success" onclick="downloadExtraction()">
                        <i class="bi bi-download"></i> Download JSON
                    </button>
                </div>
                <div class="result-content">
                    <div class="markdown-preview">
                        <pre><code>${escapeHtml(jsonStr)}</code></pre>
                    </div>
                </div>
            </div>
        `;
        // Store extraction for download
        window.currentExtraction = result.extraction;
    } else if (result.status === 'partial' && result.raw_extraction) {
        extractionHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div class="result-info">
                        <i class="bi bi-cpu"></i>
                        <div>
                            <div class="result-filename">LLM Extraction Result (Partial)</div>
                            <div class="result-meta">Model: ${result.model} | Could not parse as JSON</div>
                        </div>
                    </div>
                </div>
                <div class="result-content">
                    <div class="markdown-preview">
                        <pre><code>${escapeHtml(result.raw_extraction)}</code></pre>
                    </div>
                </div>
            </div>
        `;
        window.currentExtraction = result.raw_extraction;
    } else {
        extractionHTML = `
            <div class="error-message">
                <i class="bi bi-exclamation-triangle"></i>
                <h3>Extraction Failed</h3>
                <p>${result.error || 'Unknown error'}</p>
            </div>
        `;
    }

    conversionArea.innerHTML = extractionHTML;
}

// Download extraction result
function downloadExtraction() {
    if (!window.currentExtraction) {
        showToast('No extraction to download', 'error');
        return;
    }

    const content = typeof window.currentExtraction === 'string'
        ? window.currentExtraction
        : JSON.stringify(window.currentExtraction, null, 2);

    const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFilename.replace(/\.[^/.]+$/, '') + '_extraction.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Extraction downloaded!');
}

// Show confirm modal
function showConfirmModal(title, message, onConfirm) {
    const modal = document.getElementById('confirmModal');
    const titleEl = document.getElementById('confirmModalTitle');
    const bodyEl = document.getElementById('confirmModalBody');
    const confirmBtn = document.getElementById('confirmModalButton');

    titleEl.textContent = title;
    bodyEl.textContent = message;

    // Remove old event listeners
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);

    // Add new event listener
    newConfirmBtn.addEventListener('click', () => {
        onConfirm();
        bootstrap.Modal.getInstance(modal).hide();
    });

    // Show modal
    new bootstrap.Modal(modal).show();
}

// Clear session
function clearSession() {
    if (!currentSession) return;

    showConfirmModal(
        'Clear Session',
        'Clear all results from this session?',
        () => {
            currentSession.results = [];
            currentMarkdown = '';
            currentFilename = '';

            const conversionArea = document.getElementById('conversionArea');
            if (conversionArea) {
                conversionArea.innerHTML = `
                    <div class="welcome-message">
                        <h1><i class="bi bi-file-earmark-text"></i> Document Transform</h1>
                        <p>Upload PDF, DOCX, XLSX, or PPTX files to convert to Markdown</p>
                    </div>
                `;
            }

            saveSession(currentSession);
            updateSessionsList();
            showToast('Session cleared');
        }
    );
}

// Session management
function newSession() {
    const sessionId = 'session_' + Date.now();
    currentSession = {
        id: sessionId,
        title: 'New Session',
        created: new Date().toISOString(),
        results: []
    };

    sessions.unshift(currentSession);
    saveSessions();
    saveCurrentSession();
    updateSessionsList();

    // Clear UI
    const conversionArea = document.getElementById('conversionArea');
    if (conversionArea) {
        conversionArea.innerHTML = `
            <div class="welcome-message">
                <h1><i class="bi bi-file-earmark-text"></i> Document Transform</h1>
                <p>Upload PDF, DOCX, XLSX, or PPTX files to convert to Markdown</p>
            </div>
        `;
    }
}

function loadSessions() {
    const stored = localStorage.getItem(SESSIONS_KEY);
    if (stored) {
        sessions = JSON.parse(stored);
    }

    const currentId = localStorage.getItem(CURRENT_SESSION_KEY);
    if (currentId) {
        currentSession = sessions.find(s => s.id === currentId);
    }

    if (!currentSession && sessions.length > 0) {
        currentSession = sessions[0];
    }

    updateSessionsList();
}

function saveSessions() {
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

function saveCurrentSession() {
    if (currentSession) {
        localStorage.setItem(CURRENT_SESSION_KEY, currentSession.id);
    }
}

function saveSession(session) {
    const index = sessions.findIndex(s => s.id === session.id);
    if (index >= 0) {
        sessions[index] = session;
        saveSessions();
    }
}

function updateSessionsList() {
    const sessionsList = document.getElementById('sessionsList');
    if (!sessionsList) return;

    sessionsList.innerHTML = sessions.map(session => {
        const isActive = currentSession && session.id === currentSession.id;
        const date = new Date(session.created);
        const resultsCount = session.results.length;

        return `
            <div class="session-item ${isActive ? 'active' : ''}" onclick="selectSession('${session.id}')">
                <div class="session-icon">📄</div>
                <div class="session-details">
                    <div class="session-title">${session.title}</div>
                    <div class="session-meta">${resultsCount} files · ${date.toLocaleDateString()}</div>
                </div>
            </div>
        `;
    }).join('');
}

function selectSession(sessionId) {
    currentSession = sessions.find(s => s.id === sessionId);
    if (currentSession) {
        saveCurrentSession();
        updateSessionsList();
        loadSessionResults();
    }
}

function loadSessionResults() {
    const conversionArea = document.getElementById('conversionArea');
    if (!conversionArea || !currentSession) return;

    if (currentSession.results.length === 0) {
        conversionArea.innerHTML = `
            <div class="welcome-message">
                <h1><i class="bi bi-file-earmark-text"></i> Document Transform</h1>
                <p>Upload PDF, DOCX, XLSX, or PPTX files to convert to Markdown</p>
            </div>
        `;
        return;
    }

    const lastResult = currentSession.results[currentSession.results.length - 1];
    currentMarkdown = lastResult.markdown;
    currentFilename = lastResult.filename;
    displayMarkdown(currentMarkdown, currentFilename);
}

function filterSessions() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    const query = searchInput.value.toLowerCase();
    const sessionItems = document.querySelectorAll('.session-item');

    sessionItems.forEach(item => {
        const title = item.querySelector('.session-title').textContent.toLowerCase();
        item.style.display = title.includes(query) ? 'flex' : 'none';
    });
}

// Settings
function loadSettings() {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
        settings = { ...settings, ...JSON.parse(stored) };
    }

    // Apply settings to UI
    const apiKeyInput = document.getElementById('apiKeyInput');
    const useOcrCheck = document.getElementById('useOcrCheck');
    const detectTablesCheck = document.getElementById('detectTablesCheck');
    const ocrLanguageSelect = document.getElementById('ocrLanguageSelect');

    if (apiKeyInput) apiKeyInput.value = settings.apiKey;
    if (useOcrCheck) useOcrCheck.checked = settings.useOcr;
    if (detectTablesCheck) detectTablesCheck.checked = settings.detectTables;
    if (ocrLanguageSelect) ocrLanguageSelect.value = settings.ocrLanguage;
}

function saveSettings() {
    const apiKeyInput = document.getElementById('apiKeyInput');
    const useOcrCheck = document.getElementById('useOcrCheck');
    const detectTablesCheck = document.getElementById('detectTablesCheck');
    const ocrLanguageSelect = document.getElementById('ocrLanguageSelect');

    settings.apiKey = apiKeyInput ? apiKeyInput.value : '';
    settings.useOcr = useOcrCheck ? useOcrCheck.checked : true;
    settings.detectTables = detectTablesCheck ? detectTablesCheck.checked : true;
    settings.ocrLanguage = ocrLanguageSelect ? ocrLanguageSelect.value : 'en';

    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
    showToast('Settings saved successfully!');
    closeSettings();
}

// UI functions
function toggleSidebar() {
    console.log('toggleSidebar called');
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');
    const sidebarIcon = document.getElementById('sidebarIcon');
    const topbarIcon = document.getElementById('topbarIcon');

    if (!sidebar) {
        console.error('Sidebar element not found');
        return;
    }

    const isCollapsed = sidebar.classList.toggle('collapsed');
    console.log('Sidebar toggled - isCollapsed:', isCollapsed);

    if (sidebarIcon) {
        sidebarIcon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
    }
    if (topbarIcon) {
        topbarIcon.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(180deg)';
    }

    if (window.innerWidth <= 768) {
        if (mobileOverlay) {
            mobileOverlay.classList.toggle('active', !isCollapsed);
        }
    }
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');

    if (sidebar && !sidebar.classList.contains('collapsed')) {
        sidebar.classList.add('collapsed');
        if (mobileOverlay) mobileOverlay.classList.remove('active');
    }
}

function openSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.add('active');
        loadSettings();
    }
}

function closeSettings() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function closeModalOnOverlay(event) {
    if (event.target.id === 'settingsModal') {
        closeSettings();
    }
}

function showSettingsSection(sectionName) {
    const sections = document.querySelectorAll('.settings-section');
    const buttons = document.querySelectorAll('.modal-section-btn');

    sections.forEach(section => {
        section.classList.remove('active');
    });

    buttons.forEach(button => {
        button.classList.remove('active');
    });

    const sectionId = sectionName + 'Settings';
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add('active');
    }

    const button = event?.target;
    if (button) {
        button.classList.add('active');
    }
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toastNotification');
    const toastMessage = document.getElementById('toastMessage');

    if (!toast || !toastMessage) return;

    toastMessage.textContent = message;
    toast.className = 'toast-notification ' + type;
    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Cmd/Ctrl + K: Toggle sidebar
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        toggleSidebar();
    }

    // Cmd/Ctrl + ,: Open settings
    if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        openSettings();
    }

    // Escape: Close modals/sidebar
    if (e.key === 'Escape') {
        closeSettings();
        if (window.innerWidth <= 768) {
            closeSidebar();
        }
    }
});
