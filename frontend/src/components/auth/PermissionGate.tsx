import React from 'react'
import { Navigate } from 'react-router-dom'
import { Result, Button } from 'antd'
import { useAuthorization } from '../../hooks/useAuthorization'

interface PermissionGateProps {
  children: React.ReactNode
  requiredPermissions?: string[]
  requireAdmin?: boolean
  redirectTo?: string
  showFallback?: boolean
}

const PermissionGate: React.FC<PermissionGateProps> = ({
  children,
  requiredPermissions = [],
  requireAdmin = false,
  redirectTo = '/dashboard',
  showFallback = true,
}) => {
  const { isAuthenticated, isAdmin, hasAllPermissions } = useAuthorization()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  const lacksAdmin = requireAdmin && !isAdmin
  const lacksPermissions =
    requiredPermissions.length > 0 && !hasAllPermissions(requiredPermissions)

  if (!lacksAdmin && !lacksPermissions) {
    return <>{children}</>
  }

  if (!showFallback) {
    return <Navigate to={redirectTo} replace />
  }

  return (
    <Result
      status="403"
      title="Insufficient Permissions"
      subTitle="You do not have access to view this section."
      extra={
        <Button type="primary" href={redirectTo}>
          Return to Dashboard
        </Button>
      }
    />
  )
}

export default PermissionGate
