export interface ElectronAPI {
  // Window controls
  window: {
    minimize: () => void
    maximize: () => void
    close: () => void
    isMaximized: () => Promise<boolean>
  }
  
  // Print functionality
  print: {
    printPage: (options?: any) => Promise<{ success: boolean; message: string }>
    printToPDF: (options?: any) => Promise<{ success: boolean; message: string; filePath?: string }>
    showPrintPreview: (url: string) => Promise<{ success: boolean; message: string }>
  }
  
  // Update functionality
  checkForUpdates: () => void
  
  // Legacy window controls (for compatibility)
  minimize?: () => void
  maximize?: () => void
  close?: () => void
  
  // Splash screen progress
  onProgressUpdate?: (callback: (progress: number, message: string) => void) => void
  removeProgressListener?: () => void
  sendProgress?: (progress: number, message: string) => void
  
  // Menu actions
  onMenuAction?: (callback: (action: string) => void) => void
  removeMenuListener?: () => void
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}

export {}
