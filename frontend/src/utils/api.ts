import axios, { AxiosHeaders } from 'axios'

import { getOrCreateDeviceId } from './deviceId'

// Get Flask API base URL
// In Electron, get port from electronAPI
// In web browser, use relative URLs (dev mode with proxy)
async function getBaseURL(): Promise<string> {
  if (window.electronAPI && window.electronAPI.getFlaskPort) {
    try {
      const port = await window.electronAPI.getFlaskPort()
      return `http://127.0.0.1:${port}`
    } catch (error) {
      console.error('[API] Failed to get Flask port from Electron:', error)
      return 'http://127.0.0.1:5000' // Fallback
    }
  }
  // In development/web mode, use empty baseURL for proxy
  return ''
}

// Create axios instance
const apiClient = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable sending cookies with requests for Flask session
})

// Initialize baseURL
let isInitialized = false

async function initializeAPI() {
  if (!isInitialized) {
    const baseURL = await getBaseURL()
    apiClient.defaults.baseURL = baseURL
    isInitialized = true
    console.log('[API] Initialized with baseURL:', baseURL)
  }
}

// Request interceptor - ensure API is initialized before each request
apiClient.interceptors.request.use(
  async (config) => {
    await initializeAPI()
    const deviceId = getOrCreateDeviceId()
    if (deviceId) {
      const maybeHeaders = config.headers as AxiosHeaders | undefined
      if (maybeHeaders && typeof maybeHeaders.set === 'function') {
        maybeHeaders.set('X-Device-Id', deviceId)
      } else {
        config.headers = {
          ...(config.headers || {}),
          'X-Device-Id': deviceId,
        }
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('[API Error]', error.response.status, error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('[API Error] No response from server')
    } else {
      // Error in request setup
      console.error('[API Error]', error.message)
    }
    return Promise.reject(error)
  }
)

export default apiClient
