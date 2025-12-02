import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import apiClient from '../utils/api'
import { getOrCreateDeviceId } from '../utils/deviceId'

interface User {
  id: number
  username: string
  email: string
  role: string
  permissions: string[]
  is_admin?: boolean
}

export interface LoginFeedbackStep {
  key: string
  label: string
  status: 'success' | 'pending' | 'error' | 'skipped'
  detail?: string
}

export interface LoginFeedback {
  attemptId: string
  finalStatus: string
  steps: LoginFeedbackStep[]
  timestamp?: string
  context?: Record<string, any>
}

export interface LoginResult {
  feedback?: LoginFeedback
}

export interface LoginError extends Error {
  code?: string
  feedback?: LoginFeedback
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string, rememberMe?: boolean) => Promise<LoginResult>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  hasPermission: (permission: string) => boolean
  hasAnyPermission: (permissions: string[]) => boolean
  hasAllPermissions: (permissions: string[]) => boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

const normalizeLoginFeedback = (rawFeedback: any): LoginFeedback | undefined => {
  if (!rawFeedback) {
    return undefined
  }

  const steps: LoginFeedbackStep[] = Array.isArray(rawFeedback.steps)
    ? rawFeedback.steps.map((step: any) => ({
        key: step?.key || step?.label || 'step',
        label: step?.label || step?.key || 'Step',
        status: (step?.status || 'pending') as LoginFeedbackStep['status'],
        detail: step?.detail || '',
      }))
    : []

  return {
    attemptId: rawFeedback.attempt_id || rawFeedback.attemptId || 'attempt',
    finalStatus: rawFeedback.final_status || rawFeedback.finalStatus || 'unknown',
    steps,
    timestamp: rawFeedback.timestamp,
    context: rawFeedback.context,
  }
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const normalizePermissions = (perms?: string[]): string[] => {
    if (!Array.isArray(perms)) {
      return []
    }

    const cleaned = perms
      .map((perm) => (perm || '').trim())
      .filter((perm) => perm.length > 0)

    return Array.from(new Set(cleaned))
  }

  const mapUserResponse = (rawUser: any): User => {
    const safeRole = typeof rawUser?.role === 'string' ? rawUser.role : 'user'
    return {
      id: Number(rawUser?.id ?? 0),
      username: rawUser?.username || '',
      email: rawUser?.email || '',
      role: safeRole,
      permissions: normalizePermissions(rawUser?.permissions),
      is_admin: Boolean(rawUser?.is_admin),
    }
  }

  const checkAuth = async () => {
    try {
      const response = await apiClient.get('/api/v1/auth/me')
      // API response structure: { data: {...user data...} }
      setUser(mapUserResponse(response.data.data))
    } catch (error) {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (username: string, password: string, rememberMe = false): Promise<LoginResult> => {
    try {
      setIsLoading(true)
      const response = await apiClient.post('/api/v1/auth/login', {
        username,
        password,
        remember_me: rememberMe,
        device_id: getOrCreateDeviceId(),
      })

      const feedback = normalizeLoginFeedback(response?.data?.meta?.login_feedback)
      // API response structure: { data: { user: {...} }, message: '...' }
      if (response?.data?.data?.user) {
        setUser(mapUserResponse(response.data.data.user))
      }
      message.success('Login successful!')
      return { feedback }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Invalid username or password'
      const feedback = normalizeLoginFeedback(error.response?.data?.meta?.login_feedback)
      const enrichedError = new Error(errorMessage) as LoginError
      enrichedError.code = error.response?.data?.error
      enrichedError.feedback = feedback
      message.error(errorMessage)
      throw enrichedError
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await apiClient.post('/api/v1/auth/logout')
      setUser(null)
      message.success('Logged out successfully')
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const isAdmin = Boolean(
    user && (user.is_admin || user.role?.toLowerCase() === 'admin' || user.permissions?.includes('admin.full'))
  )

  const hasPermission = (permission: string) => {
    if (!permission) return false
    if (!user) return false
    if (isAdmin) return true
    return user.permissions.includes(permission)
  }

  const hasAnyPermission = (permissions: string[]) => {
    if (!permissions || permissions.length === 0) {
      return false
    }
    return permissions.some((permission) => hasPermission(permission))
  }

  const hasAllPermissions = (permissions: string[]) => {
    if (!permissions || permissions.length === 0) {
      return false
    }
    return permissions.every((permission) => hasPermission(permission))
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    checkAuth,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin,
  }

  // Show loading screen while checking initial authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        backgroundColor: '#f0f2f5'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <svg width="50" height="50" viewBox="0 0 50 50" style={{ animation: 'spin 1s linear infinite' }}>
            <circle cx="25" cy="25" r="20" fill="none" stroke="#1890ff" strokeWidth="4" strokeDasharray="80, 200" strokeLinecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 25 25" to="360 25 25" dur="1s" repeatCount="indefinite" />
            </circle>
          </svg>
        </div>
        <div style={{ fontSize: '16px', color: '#595959' }}>Loading AMRS Maintenance Tracker...</div>
        <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>Initializing application...</div>
      </div>
    )
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
