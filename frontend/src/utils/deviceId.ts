const STORAGE_KEY = 'amrs-device-id'
const MAX_LENGTH = 64

function clamp(value: string): string {
  if (!value) {
    return value
  }
  return value.slice(0, MAX_LENGTH)
}

function fallbackId(): string {
  const prefix = 'device-'
  // Prefer crypto.randomUUID for stable, unique IDs
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return clamp(crypto.randomUUID())
  }

  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const array = new Uint32Array(4)
    crypto.getRandomValues(array)
    const randomPart = Array.from(array)
      .map((value) => value.toString(16).padStart(8, '0'))
      .join('')
    return clamp(`${prefix}${randomPart}`)
  }

  const randomString = Math.random().toString(36).slice(2)
  return clamp(`${prefix}${Date.now().toString(36)}-${randomString}`)
}

export function getOrCreateDeviceId(): string {
  const generated = fallbackId()
  if (typeof window === 'undefined') {
    return generated
  }

  try {
    const existing = window.localStorage?.getItem(STORAGE_KEY)
    if (existing && existing.trim()) {
      return clamp(existing.trim())
    }
    window.localStorage?.setItem(STORAGE_KEY, generated)
    return generated
  } catch (error) {
    console.warn('[deviceId] Failed to access localStorage, using fallback id.', error)
    return generated
  }
}

export function clearStoredDeviceId(): void {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage?.removeItem(STORAGE_KEY)
  } catch (error) {
    console.warn('[deviceId] Failed to clear device id from localStorage.', error)
  }
}

export { STORAGE_KEY as DEVICE_ID_STORAGE_KEY }
