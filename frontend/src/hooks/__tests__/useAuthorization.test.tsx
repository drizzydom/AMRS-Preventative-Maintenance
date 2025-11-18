import { renderHook } from '@testing-library/react'
import { useAuthorization } from '../useAuthorization'
import { useAuth } from '../../contexts/AuthContext'

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}))

const mockedUseAuth = useAuth as jest.Mock

describe('useAuthorization', () => {
  beforeEach(() => {
    mockedUseAuth.mockReturnValue({
      user: { role: 'Manager' },
      isAuthenticated: true,
      isAdmin: false,
      hasPermission: jest.fn().mockReturnValue(true),
      hasAnyPermission: jest.fn().mockReturnValue(true),
      hasAllPermissions: jest.fn().mockReturnValue(true),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('reports role matches regardless of case', () => {
    const { result } = renderHook(() => useAuthorization())
    expect(result.current.hasRole('manager')).toBe(true)
    expect(result.current.hasRole(['admin', 'manager'])).toBe(true)
    expect(result.current.hasRole('technician')).toBe(false)
  })

  it('exposes memoized helpers from context', () => {
    const { result, rerender } = renderHook(() => useAuthorization())
    const first = result.current
    rerender()
    expect(result.current).toBe(first)
    expect(first.isAuthenticated).toBe(true)
    expect(first.hasPermission('machines.view')).toBe(true)
  })
})
