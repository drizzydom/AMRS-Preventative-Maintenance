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
