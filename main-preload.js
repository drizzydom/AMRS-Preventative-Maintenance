const { contextBridge, ipcRenderer } = require('electron');

// Expose print functionality and window controls to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Window controls
    window: {
        minimize: () => ipcRenderer.send('minimize-window'),
        maximize: () => ipcRenderer.send('maximize-window'),
        close: () => ipcRenderer.send('close-window'),
        isMaximized: () => ipcRenderer.invoke('is-maximized')
    },
    
    // Print functionality
    print: {
        // Print the current page
        printPage: (options) => ipcRenderer.invoke('print-page', options),
        
        // Generate and save PDF
        printToPDF: (options) => ipcRenderer.invoke('print-to-pdf', options),
        
        // Show print preview window
        showPrintPreview: (url) => ipcRenderer.invoke('show-print-preview', url)
    },
    
    // Update functionality (existing)
    checkForUpdates: () => ipcRenderer.send('check-for-updates'),
    
    // Flask API configuration
    getFlaskPort: () => ipcRenderer.invoke('get-flask-port')
});

// Add event listeners when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
    // Add print button functionality to existing print links
    addPrintButtonHandlers();
    
    // Add CSS for print functionality
    addPrintStyles();
    
    // Ensure all print-related CSS is loaded
    ensurePrintCSSLoaded();
});

function ensurePrintCSSLoaded() {
    // Check if print.css is loaded, if not, load it
    const printCSSExists = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
        .some(link => link.href.includes('print.css'));
    
    if (!printCSSExists) {
        const printCSS = document.createElement('link');
        printCSS.rel = 'stylesheet';
        printCSS.href = '/static/css/print.css';
        document.head.appendChild(printCSS);
    }
}

function addPrintButtonHandlers() {
    // Find all existing print links and add electron print functionality
    const printLinks = document.querySelectorAll('a[href*="/print"], a[href*="print-view"]');
    
    printLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const originalHref = link.href;
            
            // Show context menu for print options
            const printOptions = await showPrintOptionsMenu();
            
            if (printOptions.cancelled) {
                return;
            }
            
            if (printOptions.action === 'preview') {
                // Open print preview in new window
                await window.electronAPI.print.showPrintPreview(originalHref);
            } else if (printOptions.action === 'pdf') {
                // Navigate to print page and generate PDF after ensuring content is loaded
                await navigateAndExecute(originalHref, async () => {
                    const result = await window.electronAPI.print.printToPDF(printOptions.pdfOptions);
                    if (result.success) {
                        showNotification('PDF saved successfully!', 'success');
                    } else {
                        showNotification(`PDF generation failed: ${result.message}`, 'error');
                    }
                });
            } else if (printOptions.action === 'print') {
                // Navigate to print page and print directly after ensuring content is loaded
                await navigateAndExecute(originalHref, async () => {
                    const result = await window.electronAPI.print.printPage(printOptions.printOptions);
                    if (result.success) {
                        showNotification('Print completed successfully!', 'success');
                    } else {
                        showNotification(`Print failed: ${result.message}`, 'error');
                    }
                });
            }
        });
    });
}

async function navigateAndExecute(url, executeFunction) {
    // Navigate to the print URL
    window.location.href = url;
    
    // Wait for the page to load and all CSS to be applied
    await new Promise(resolve => {
        if (document.readyState === 'complete') {
            resolve();
        } else {
            window.addEventListener('load', resolve);
        }
    });
    
    // Wait a bit more for CSS to be fully applied
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Execute the print/PDF function
    await executeFunction();
}

function addPrintStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Print options modal */
        .electron-print-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        }
        
        .electron-print-content {
            background: white;
            padding: 20px;
            border-radius: 8px;
            max-width: 400px;
            width: 90%;
        }
        
        .electron-print-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        .electron-print-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            flex: 1;
        }
        
        .electron-print-btn.primary {
            background: #007bff;
            color: white;
        }
        
        .electron-print-btn.secondary {
            background: #6c757d;
            color: white;
        }
        
        .electron-print-btn.success {
            background: #28a745;
            color: white;
        }
        
        .electron-print-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            z-index: 10001;
            max-width: 300px;
        }
        
        .electron-print-notification.success {
            background: #28a745;
        }
        
        .electron-print-notification.error {
            background: #dc3545;
        }
    `;
    document.head.appendChild(style);
}

function showPrintOptionsMenu() {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'electron-print-modal';
        modal.innerHTML = `
            <div class="electron-print-content">
                <h3>Print Options</h3>
                <p>Choose how you want to print this document:</p>
                
                <div class="electron-print-buttons">
                    <button class="electron-print-btn primary" data-action="preview">
                        Preview
                    </button>
                    <button class="electron-print-btn success" data-action="pdf">
                        Save as PDF
                    </button>
                    <button class="electron-print-btn primary" data-action="print">
                        Print
                    </button>
                    <button class="electron-print-btn secondary" data-action="cancel">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        modal.addEventListener('click', (e) => {
            if (e.target.classList.contains('electron-print-btn')) {
                const action = e.target.dataset.action;
                
                document.body.removeChild(modal);
                
                if (action === 'cancel') {
                    resolve({ cancelled: true });
                } else {
                    resolve({
                        cancelled: false,
                        action: action,
                        printOptions: {
                            printBackground: true,
                            color: true,
                            margin: { marginType: 'printableArea' }
                        },
                        pdfOptions: {
                            printBackground: true,
                            pageSize: 'A4',
                            marginsType: 0
                        }
                    });
                }
            }
        });
    });
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `electron-print-notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (document.body.contains(notification)) {
            document.body.removeChild(notification);
        }
    }, 3000);
}