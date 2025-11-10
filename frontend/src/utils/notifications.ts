/**
 * Native notification utilities for desktop app
 * Handles both browser and Electron notifications
 */

/**
 * Request notification permission if not already granted
 */
export const requestNotificationPermission = async (): Promise<NotificationPermission> => {
  if (!('Notification' in window)) {
    console.warn('[Notifications] Notification API not supported')
    return 'denied'
  }

  if (Notification.permission === 'granted') {
    return 'granted'
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission()
    return permission
  }

  return Notification.permission
}

interface NotificationOptions {
  body?: string
  icon?: string
  badge?: string
  tag?: string
  requireInteraction?: boolean
  silent?: boolean
}

/**
 * Show a native notification
 * @param title - Notification title
 * @param options - Notification options
 * @returns Notification instance or null if permission denied
 */
export const showNativeNotification = async (
  title: string,
  options: NotificationOptions = {}
): Promise<Notification | null> => {
  // Request permission if needed
  const permission = await requestNotificationPermission()

  if (permission !== 'granted') {
    console.warn('[Notifications] Permission denied, cannot show notification')
    return null
  }

  try {
    const notification = new Notification(title, {
      body: options.body,
      icon: options.icon || '/icon.png', // Default app icon
      badge: options.badge,
      tag: options.tag,
      requireInteraction: options.requireInteraction || false,
      silent: options.silent || false,
    })

    // Auto-close after 5 seconds unless requireInteraction is true
    if (!options.requireInteraction) {
      setTimeout(() => notification.close(), 5000)
    }

    return notification
  } catch (error) {
    console.error('[Notifications] Failed to show notification:', error)
    return null
  }
}

/**
 * Show notification for overdue maintenance items
 */
export const notifyOverdueItems = async (count: number) => {
  if (count === 0) return

  await showNativeNotification('Maintenance Overdue', {
    body: `${count} item${count > 1 ? 's' : ''} need${count === 1 ? 's' : ''} immediate attention`,
    tag: 'overdue-maintenance',
    requireInteraction: true, // Keep notification visible until user interacts
  })
}

/**
 * Show notification for due soon items
 */
export const notifyDueSoonItems = async (count: number) => {
  if (count === 0) return

  await showNativeNotification('Maintenance Due Soon', {
    body: `${count} item${count > 1 ? 's are' : ' is'} due within 7 days`,
    tag: 'due-soon-maintenance',
    silent: true, // Less urgent, silent notification
  })
}

/**
 * Show notification for sync events
 */
export const notifySyncEvent = async (message: string = 'Data synchronized') => {
  await showNativeNotification('Sync Update', {
    body: message,
    tag: 'sync-event',
    silent: true,
  })
}

/**
 * Show notification for new maintenance record created
 */
export const notifyMaintenanceCreated = async (machineName: string, partName: string) => {
  await showNativeNotification('Maintenance Recorded', {
    body: `Maintenance for ${partName} on ${machineName} has been recorded`,
    tag: 'maintenance-created',
    silent: true,
  })
}

/**
 * Show notification for error/warning
 */
export const notifyError = async (message: string) => {
  await showNativeNotification('Error', {
    body: message,
    tag: 'error',
    requireInteraction: true,
  })
}

/**
 * Initialize notifications (request permission on first launch)
 */
export const initializeNotifications = async () => {
  const permission = await requestNotificationPermission()
  console.log('[Notifications] Permission status:', permission)
  return permission
}
