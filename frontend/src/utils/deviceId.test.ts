import { clearStoredDeviceId, getOrCreateDeviceId, DEVICE_ID_STORAGE_KEY } from './deviceId'

describe('deviceId utility', () => {
  beforeEach(() => {
    clearStoredDeviceId()
    window.localStorage?.removeItem(DEVICE_ID_STORAGE_KEY)
    jest.restoreAllMocks()
  })

  it('returns a stable device id once generated', () => {
    const first = getOrCreateDeviceId()
    expect(first).toBeTruthy()
    const stored = window.localStorage.getItem(DEVICE_ID_STORAGE_KEY)
    expect(stored).toBe(first)

    const second = getOrCreateDeviceId()
    expect(second).toBe(first)
    expect(second.length).toBeLessThanOrEqual(64)
  })

  it('falls back gracefully when localStorage access fails', () => {
    const originalStorage = window.localStorage

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: {
        getItem: () => {
          throw new Error('denied')
        },
        setItem: () => {
          throw new Error('denied')
        },
        removeItem: () => undefined,
      },
    })

    expect(() => getOrCreateDeviceId()).not.toThrow()

    Object.defineProperty(window, 'localStorage', {
      configurable: true,
      value: originalStorage,
    })
  })
})
