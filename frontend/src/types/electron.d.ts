export interface ElectronAPI {
  minimize: () => void
  maximize: () => void
  close: () => void
  onProgressUpdate: (callback: (progress: number, message: string) => void) => void
  removeProgressListener: () => void
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}

export {}
