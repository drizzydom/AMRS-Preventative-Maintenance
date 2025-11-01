/**
 * Permission constants and utilities
 * Phase 4.1 - RBAC Implementation
 */

export const PERMISSIONS = {
  // Machine permissions
  MACHINES_VIEW: 'machines.view',
  MACHINES_CREATE: 'machines.create',
  MACHINES_EDIT: 'machines.edit',
  MACHINES_DELETE: 'machines.delete',

  // Maintenance permissions
  MAINTENANCE_VIEW: 'maintenance.view',
  MAINTENANCE_CREATE: 'maintenance.create',
  MAINTENANCE_EDIT: 'maintenance.edit',
  MAINTENANCE_DELETE: 'maintenance.delete',
  MAINTENANCE_COMPLETE: 'maintenance.complete',

  // Audit permissions
  AUDITS_VIEW: 'audits.view',
  AUDITS_CREATE: 'audits.create',
  AUDITS_EDIT: 'audits.edit',
  AUDITS_DELETE: 'audits.delete',

  // Site permissions
  SITES_VIEW: 'sites.view',
  SITES_CREATE: 'sites.create',
  SITES_EDIT: 'sites.edit',
  SITES_DELETE: 'sites.delete',

  // User management permissions
  USERS_VIEW: 'users.view',
  USERS_CREATE: 'users.create',
  USERS_EDIT: 'users.edit',
  USERS_DELETE: 'users.delete',

  // Reports permissions
  REPORTS_VIEW: 'reports.view',
  REPORTS_GENERATE: 'reports.generate',
  REPORTS_EXPORT: 'reports.export',

  // Settings permissions
  SETTINGS_VIEW: 'settings.view',
  SETTINGS_EDIT: 'settings.edit',
} as const

export const ROLES = {
  ADMINISTRATOR: 'Administrator',
  MANAGER: 'Manager',
  TECHNICIAN: 'Technician',
  VIEWER: 'Viewer',
} as const

// Default permissions for each role
export const ROLE_PERMISSIONS: Record<string, string[]> = {
  [ROLES.ADMINISTRATOR]: Object.values(PERMISSIONS),
  [ROLES.MANAGER]: [
    PERMISSIONS.MACHINES_VIEW,
    PERMISSIONS.MACHINES_CREATE,
    PERMISSIONS.MACHINES_EDIT,
    PERMISSIONS.MAINTENANCE_VIEW,
    PERMISSIONS.MAINTENANCE_CREATE,
    PERMISSIONS.MAINTENANCE_EDIT,
    PERMISSIONS.MAINTENANCE_COMPLETE,
    PERMISSIONS.AUDITS_VIEW,
    PERMISSIONS.AUDITS_CREATE,
    PERMISSIONS.AUDITS_EDIT,
    PERMISSIONS.SITES_VIEW,
    PERMISSIONS.REPORTS_VIEW,
    PERMISSIONS.REPORTS_GENERATE,
    PERMISSIONS.REPORTS_EXPORT,
    PERMISSIONS.SETTINGS_VIEW,
  ],
  [ROLES.TECHNICIAN]: [
    PERMISSIONS.MACHINES_VIEW,
    PERMISSIONS.MAINTENANCE_VIEW,
    PERMISSIONS.MAINTENANCE_COMPLETE,
    PERMISSIONS.AUDITS_VIEW,
    PERMISSIONS.SITES_VIEW,
    PERMISSIONS.SETTINGS_VIEW,
  ],
  [ROLES.VIEWER]: [
    PERMISSIONS.MACHINES_VIEW,
    PERMISSIONS.MAINTENANCE_VIEW,
    PERMISSIONS.AUDITS_VIEW,
    PERMISSIONS.SITES_VIEW,
    PERMISSIONS.REPORTS_VIEW,
    PERMISSIONS.SETTINGS_VIEW,
  ],
}

export const checkPermission = (userPermissions: string[], permission: string): boolean => {
  return userPermissions.includes(permission)
}

export const checkAnyPermission = (userPermissions: string[], permissions: string[]): boolean => {
  return permissions.some(permission => userPermissions.includes(permission))
}

export const checkAllPermissions = (userPermissions: string[], permissions: string[]): boolean => {
  return permissions.every(permission => userPermissions.includes(permission))
}
