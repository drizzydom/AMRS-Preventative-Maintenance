import { useMemo } from 'react'
import { useAuth } from '../contexts/AuthContext'

/**
 * Convenience hook that exposes commonly used authorization helpers so pages
 * and components do not have to re-implement role/permission logic.
 */
export const useAuthorization = () => {
  const {
    user,
    isAuthenticated,
    isAdmin,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
  } = useAuth()

  const hasRole = (roles: string | string[]) => {
    if (!user) {
      return false
    }

    const roleList = Array.isArray(roles) ? roles : [roles]
    return roleList
      .filter(Boolean)
      .map((role) => role.toLowerCase())
      .some((role) => user.role?.toLowerCase() === role)
  }

  const authorization = useMemo(
    () => ({
      user,
      isAuthenticated,
      isAdmin,
      hasRole,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
    }),
    [
      user,
      isAuthenticated,
      isAdmin,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
    ]
  )

  return authorization
}

export type AuthorizationHelpers = ReturnType<typeof useAuthorization>
