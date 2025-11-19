import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import Sidebar from '../Sidebar'

type AuthHook = {
  user: {
    username: string
    role: string
    is_admin?: boolean
  } | null
  logout: () => Promise<void> | void
}

const mockLogout = jest.fn()

jest.mock('../../hooks/useAuthorization', () => ({
  useAuthorization: () => ({
    isAdmin: true,
    hasPermission: () => true,
  }),
}))

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: (): AuthHook => ({
    user: {
      username: 'maintenance.lead',
      role: 'technician',
    },
    logout: mockLogout,
  }),
}))

const mockNavigate = jest.fn()

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/dashboard' }),
}))

describe('Sidebar', () => {
  beforeEach(() => {
    mockLogout.mockClear()
    mockNavigate.mockClear()
  })

  it('renders the logout button and calls logout when clicked', () => {
    render(<Sidebar />)
    const logoutButton = screen.getByRole('button', { name: /logout/i })
    fireEvent.click(logoutButton)
    expect(mockLogout).toHaveBeenCalledTimes(1)
  })
})
