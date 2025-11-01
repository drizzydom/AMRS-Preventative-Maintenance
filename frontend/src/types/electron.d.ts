export interface ElectronAPI {
  // Window controls
  minimize: () => void
  maximize: () => void
  close: () => void
  
  // Splash screen progress
  onProgressUpdate: (callback: (progress: number, message: string) => void) => void
  removeProgressListener: () => void
  sendProgress: (progress: number, message: string) => void
  
  // Menu actions
  onMenuAction: (callback: (action: string) => void) => void
  removeMenuListener: () => void
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}

export {}
