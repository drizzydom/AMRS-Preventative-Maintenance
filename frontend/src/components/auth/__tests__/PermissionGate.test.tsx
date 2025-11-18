import React from 'react'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import PermissionGate from '../PermissionGate'
import { useAuthorization } from '../../../hooks/useAuthorization'

jest.mock('../../../hooks/useAuthorization', () => ({
  useAuthorization: jest.fn(),
}))

const mockUseAuthorization = useAuthorization as jest.MockedFunction<typeof useAuthorization>

const LocationDisplay = () => {
  const location = useLocation()
  return <div data-testid="location-display">{location.pathname}</div>
}

describe('PermissionGate', () => {
  beforeEach(() => {
    mockUseAuthorization.mockReturnValue({
      user: { role: 'admin' },
      isAuthenticated: true,
      isAdmin: true,
      hasAllPermissions: jest.fn().mockReturnValue(true),
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('renders children when authorized', () => {
    render(
      <MemoryRouter>
        <PermissionGate requiredPermissions={['reports.view']}>
          <div>Reports Content</div>
        </PermissionGate>
      </MemoryRouter>
    )

    expect(screen.getByText('Reports Content')).toBeInTheDocument()
  })

  it('shows fallback when permissions are missing', () => {
    mockUseAuthorization.mockReturnValue({
      user: { role: 'tech' },
      isAuthenticated: true,
      isAdmin: false,
      hasAllPermissions: jest.fn().mockReturnValue(false),
    })

    render(
      <MemoryRouter>
        <PermissionGate requiredPermissions={['reports.view']}>
          <div>Hidden</div>
        </PermissionGate>
      </MemoryRouter>
    )

    expect(screen.getByText('Insufficient Permissions')).toBeInTheDocument()
  })

  it('redirects to login when unauthenticated', () => {
    mockUseAuthorization.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isAdmin: false,
      hasAllPermissions: jest.fn().mockReturnValue(false),
    })

    render(
      <MemoryRouter initialEntries={['/reports']}>
        <PermissionGate requiredPermissions={['reports.view']}>
          <div>Hidden</div>
        </PermissionGate>
        <LocationDisplay />
      </MemoryRouter>
    )

    expect(screen.getByTestId('location-display')).toHaveTextContent('/login')
  })

  it('navigates to redirect when admin required and fallback disabled', () => {
    mockUseAuthorization.mockReturnValue({
      user: { role: 'tech' },
      isAuthenticated: true,
      isAdmin: false,
      hasAllPermissions: jest.fn().mockReturnValue(true),
    })

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <PermissionGate requireAdmin showFallback={false} redirectTo="/dashboard">
          <div>Hidden</div>
        </PermissionGate>
        <LocationDisplay />
      </MemoryRouter>
    )

    expect(screen.getByTestId('location-display')).toHaveTextContent('/dashboard')
  })
})
