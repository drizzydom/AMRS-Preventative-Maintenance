const { contextBridge, ipcRenderer } = require('electron');

// Expose print functionality to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Print functionality (matching main-preload.js structure)
    print: {
        // Print the current page
        printPage: (options) => ipcRenderer.invoke('print-page', options),
        
        // Generate and save PDF
        printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),
        
        // Show print preview window
        showPrintPreview: (url) => ipcRenderer.invoke('show-print-preview', url)
    },
    
    // Close the current window (for print preview)
    closeWindow: () => ipcRenderer.invoke('close-window')
});

// Also expose the legacy electronPrint for backward compatibility
contextBridge.exposeInMainWorld('electronPrint', {
    // Print the current page
    printPage: (options) => ipcRenderer.invoke('print-page', options),
    
    // Generate and save PDF
    printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),
    
    // Show print preview window
    showPrintPreview: (url) => ipcRenderer.invoke('show-print-preview', url),
    
    // Close the current window (for print preview)
    closeWindow: () => ipcRenderer.invoke('close-window')
});

// Add print functionality when the page loads
window.addEventListener('DOMContentLoaded', () => {
    // Ensure all CSS is properly loaded first
    ensureAllCSSLoaded().then(() => {
        // Add print controls to the preview window
        addPrintControls();
        
        // Add print-specific styles
        addPrintStyles();
        
        // Fix any missing styles
        fixMissingStyles();
    });
});

async function ensureAllCSSLoaded() {
    // List of all CSS files that should be loaded based on base.html
    const requiredCSS = [
        // External CDN CSS
        'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
        
        // Local CSS files
        '/static/css/preload-fix.css',
        '/static/css/main.css',
        '/static/css/modern-ui.css',
        '/static/css/modals.css',
        '/static/css/navbar-fix.css',
        '/static/css/sidebar-fix.css',
        '/static/css/table-responsive-fix.css',
        '/static/css/admin-page-fix.css',
        '/static/css/footer-fix.css',
        '/static/css/content-position-fix.css',
        '/static/css/horizontal-scroll-enhancements.css',
        '/static/css/compact-table-layouts.css',
        '/static/css/amrs-theme.css',
        '/static/css/print.css'
    ];
    
    // Check which CSS files are missing
    const existingLinks = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
    const existingHrefs = existingLinks.map(link => link.href);
    
    const loadPromises = [];
    
    for (const cssFile of requiredCSS) {
        const isExternal = cssFile.startsWith('http');
        const fullUrl = isExternal ? cssFile : `${window.location.origin}${cssFile}`;
        
        // Check if this CSS is already loaded
        const isAlreadyLoaded = existingHrefs.some(href => 
            href === fullUrl || href.endsWith(cssFile)
        );
        
        if (!isAlreadyLoaded) {
            console.log(`[Print Preview] Loading missing CSS: ${cssFile}`);
            loadPromises.push(loadCSS(fullUrl));
        }
    }
    
    // Wait for all CSS to load
    await Promise.all(loadPromises);
    
    // Wait a bit more for CSS to be applied
    await new Promise(resolve => setTimeout(resolve, 100));
}

function loadCSS(href) {
    return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        
        link.onload = () => {
            console.log(`[Print Preview] CSS loaded: ${href}`);
            resolve();
        };
        
        link.onerror = () => {
            console.warn(`[Print Preview] Failed to load CSS: ${href}`);
            resolve(); // Don't reject, just continue
        };
        
        document.head.appendChild(link);
    });
}

function fixMissingStyles() {
    // Add inline styles to fix common missing style issues
    const fixStyles = document.createElement('style');
    fixStyles.textContent = `
        /* Ensure proper styling for print preview */
        body {
            font-family: Arial, sans-serif !important;
            line-height: 1.4 !important;
            color: #333 !important;
            background: white !important;
        }
        
        /* Ensure Bootstrap classes work */
        .container {
            max-width: 100% !important;
            padding: 0 15px !important;
        }
        
        .table {
            border-collapse: collapse !important;
            width: 100% !important;
        }
        
        .table th,
        .table td {
            border: 1px solid #dee2e6 !important;
            padding: 8px !important;
        }
        
        .table thead th {
            background-color: #f8f9fa !important;
            font-weight: bold !important;
        }
        
        /* Ensure print-specific elements are visible */
        .print-header {
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            margin-bottom: 18px !important;
            border-bottom: 2px solid #000 !important;
            padding-bottom: 12px !important;
        }
        
        .info-section {
            border: 1px solid #ddd !important;
            padding: 12px !important;
            margin-bottom: 12px !important;
            background-color: #f9f9f9 !important;
        }
        
        .section-title {
            font-size: 11pt !important;
            font-weight: bold !important;
            margin-bottom: 8px !important;
            color: #000 !important;
            border-bottom: 1px solid #ccc !important;
            padding-bottom: 3px !important;
        }
        
        .signature-section {
            border: 1px solid #333 !important;
            padding: 15px !important;
            margin-top: 20px !important;
            page-break-inside: avoid !important;
            display: flex !important;
            justify-content: space-between !important;
        }
        
        .signature-box {
            width: 45% !important;
        }
        
        .signature-line {
            border-bottom: 1px solid #000 !important;
            min-height: 30px !important;
            margin: 10px 0 5px 0 !important;
        }
        
        /* Fix any missing grid layouts */
        .info-grid {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 16px !important;
        }
        
        .info-row {
            display: flex !important;
            margin-bottom: 5px !important;
        }
        
        .info-label {
            font-weight: bold !important;
            margin-right: 10px !important;
            min-width: 100px !important;
        }
        
        .info-value {
            flex: 1 !important;
        }
    `;
    document.head.appendChild(fixStyles);
}

function addPrintControls() {
    // Create a floating print control panel
    const controlPanel = document.createElement('div');
    controlPanel.className = 'print-control-panel';
    controlPanel.innerHTML = `
        <div class="print-controls">
            <h4>Print Options</h4>
            <div class="control-buttons">
                <button id="print-direct" class="print-btn primary">
                    🖨️ Print
                </button>
                <button id="save-pdf" class="print-btn success">
                    📄 Save as PDF
                </button>
                <button id="close-preview" class="print-btn secondary">
                    ❌ Close
                </button>
            </div>
            <div class="print-options">
                <label>
                    <input type="checkbox" id="print-background" checked> Print backgrounds
                </label>
                <label>
                    <input type="checkbox" id="print-color" checked> Color printing
                </label>
                <label>
                    <input type="checkbox" id="landscape"> Landscape mode
                </label>
            </div>
        </div>
    `;
    
    document.body.appendChild(controlPanel);
    
    // Add event listeners
    document.getElementById('print-direct').addEventListener('click', async () => {
        const options = getPrintOptions();
        const result = await window.electronPrint.printPage(options);
        showMessage(result.message, result.success ? 'success' : 'error');
    });
    
    document.getElementById('save-pdf').addEventListener('click', async () => {
        const options = getPDFOptions();
        const result = await window.electronPrint.printToPDF(options);
        showMessage(result.message, result.success ? 'success' : 'error');
    });
    
    document.getElementById('close-preview').addEventListener('click', async () => {
        await window.electronPrint.closeWindow();
    });
}

function getPrintOptions() {
    return {
        printBackground: document.getElementById('print-background').checked,
        color: document.getElementById('print-color').checked,
        landscape: document.getElementById('landscape').checked,
        margin: {
            marginType: 'printableArea'
        }
    };
}

function getPDFOptions() {
    return {
        printBackground: document.getElementById('print-background').checked,
        landscape: document.getElementById('landscape').checked,
        pageSize: 'A4',
        marginsType: 0
    };
}

function showMessage(message, type) {
    const notification = document.createElement('div');
    notification.className = `print-notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 3000);
}

function addPrintStyles() {
    const printStyles = document.createElement('style');
    printStyles.textContent = `
        /* Print control panel */
        .print-control-panel {
            position: fixed;
            top: 10px;
            right: 10px;
            background: white;
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            min-width: 250px;
        }
        
        .print-controls h4 {
            margin: 0 0 10px 0;
            color: #007bff;
            font-size: 14px;
        }
        
        .control-buttons {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 10px;
        }
        
        .print-btn {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        }
        
        .print-btn.primary {
            background: #007bff;
            color: white;
        }
        
        .print-btn.primary:hover {
            background: #0056b3;
        }
        
        .print-btn.success {
            background: #28a745;
            color: white;
        }
        
        .print-btn.success:hover {
            background: #1e7e34;
        }
        
        .print-btn.secondary {
            background: #6c757d;
            color: white;
        }
        
        .print-btn.secondary:hover {
            background: #545b62;
        }
        
        .print-options {
            border-top: 1px solid #eee;
            padding-top: 10px;
        }
        
        .print-options label {
            display: block;
            margin-bottom: 5px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .print-options input[type="checkbox"] {
            margin-right: 8px;
        }
        
        .print-notification {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            padding: 10px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10001;
            font-weight: bold;
        }
        
        .print-notification.success {
            background: #28a745;
        }
        
        .print-notification.error {
            background: #dc3545;
        }
        
        /* Print-specific styles */
        @media print {
            .print-control-panel,
            .no-print,
            .navbar,
            .sidebar,
            .btn:not(.print-btn),
            button:not(.print-btn),
            .form-control,
            .pagination,
            .alert {
                display: none !important;
            }
            
            body {
                color: black !important;
                background: white !important;
            }
            
            .page-break {
                page-break-before: always;
            }
            
            .avoid-break {
                page-break-inside: avoid;
            }
            
            table {
                border-collapse: collapse;
            }
            
            th, td {
                border: 1px solid #000;
                padding: 4px;
            }
            
            .text-muted {
                color: #333 !important;
            }
        }
        
        @page {
            margin: 0.5in;
            size: auto;
        }
    `;
    document.head.appendChild(printStyles);
}