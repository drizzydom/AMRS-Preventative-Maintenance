import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { message } from 'antd'
import axios from 'axios'

interface User {
  id: number
  username: string
  email: string
  role: string
  permissions: string[]
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
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

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const checkAuth = async () => {
    try {
      const response = await axios.get('/api/v1/auth/me')
      setUser(response.data)
    } catch (error) {
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkAuth()
  }, [])

  const login = async (username: string, password: string, rememberMe = false) => {
    try {
      setIsLoading(true)
      const response = await axios.post('/api/v1/auth/login', {
        username,
        password,
        remember_me: rememberMe,
      })
      
      setUser(response.data.user)
      message.success('Login successful!')
      navigate('/dashboard')
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || 'Invalid username or password'
      message.error(errorMessage)
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await axios.post('/api/v1/auth/logout')
      setUser(null)
      message.success('Logged out successfully')
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
