import { useAuth } from '../contexts/AuthContext'

/**
 * Permission checking hook for Role-Based Access Control (RBAC)
 * Phase 4.1 - RBAC Implementation
 */

export const usePermissions = () => {
  const { user } = useAuth()

  const hasPermission = (permission: string): boolean => {
    if (!user || !user.permissions) return false
    return user.permissions.includes(permission)
  }

  const hasAnyPermission = (permissions: string[]): boolean => {
    if (!user || !user.permissions) return false
    return permissions.some(permission => user.permissions.includes(permission))
  }

  const hasAllPermissions = (permissions: string[]): boolean => {
    if (!user || !user.permissions) return false
    return permissions.every(permission => user.permissions.includes(permission))
  }

  const hasRole = (role: string): boolean => {
    if (!user) return false
    return user.role === role
  }

  const isAdmin = (): boolean => {
    return hasRole('Administrator') || hasRole('admin')
  }

  const isManager = (): boolean => {
    return hasRole('Manager') || hasRole('manager')
  }

  const isTechnician = (): boolean => {
    return hasRole('Technician') || hasRole('technician')
  }

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    isAdmin,
    isManager,
    isTechnician,
    user,
  }
}

export default usePermissions
