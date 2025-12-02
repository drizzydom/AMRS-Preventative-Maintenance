/**
 * Desktop Notification Service
 * Handles notifications for overdue and upcoming maintenance tasks
 */

import apiClient from '../utils/api'

// Check if we're in Electron environment
const isElectron = () => {
  return typeof window !== 'undefined' && (window as any).electron !== undefined
}

// Check if browser notifications are supported and permitted
const canUseNotifications = () => {
  return 'Notification' in window && Notification.permission === 'granted'
}

// Request notification permission
export const requestNotificationPermission = async (): Promise<boolean> => {
  if (!('Notification' in window)) {
    console.log('[Notifications] Not supported in this browser')
    return false
  }

  if (Notification.permission === 'granted') {
    return true
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission()
    return permission === 'granted'
  }

  return false
}

// Send a desktop notification
export const sendNotification = (title: string, options?: NotificationOptions): Notification | null => {
  if (!canUseNotifications()) {
    console.log('[Notifications] Permission not granted')
    return null
  }

  const defaultIcon = '/logo192.png'
  const notification = new Notification(title, {
    icon: defaultIcon,
    badge: defaultIcon,
    ...options,
  })

  // Handle notification click
  notification.onclick = () => {
    window.focus()
    notification.close()
  }

  return notification
}

// Notification types for maintenance
export interface MaintenanceNotification {
  id: number
  part_name: string
  machine_name: string
  site_name: string
  status: 'overdue' | 'due_soon'
  days_overdue?: number
  days_until?: number
}

// Check for overdue tasks and send notifications
export const checkOverdueTasks = async (): Promise<void> => {
  try {
    const response = await apiClient.get('/api/v1/maintenance?status=overdue')
    const overdueCount = response.data?.data?.length || 0

    if (overdueCount > 0) {
      sendNotification('⚠️ Overdue Maintenance', {
        body: `You have ${overdueCount} overdue maintenance task${overdueCount > 1 ? 's' : ''} that require attention.`,
        tag: 'overdue-maintenance', // Prevents duplicate notifications
        requireInteraction: true, // Keeps notification visible until dismissed
      })
    }
  } catch (error) {
    console.error('[Notifications] Failed to check overdue tasks:', error)
  }
}

// Check for upcoming (due soon) tasks
export const checkUpcomingTasks = async (): Promise<void> => {
  try {
    const response = await apiClient.get('/api/v1/maintenance?status=due_soon')
    const dueSoonCount = response.data?.data?.length || 0

    if (dueSoonCount > 0) {
      sendNotification('🔔 Upcoming Maintenance', {
        body: `You have ${dueSoonCount} maintenance task${dueSoonCount > 1 ? 's' : ''} due soon.`,
        tag: 'due-soon-maintenance',
      })
    }
  } catch (error) {
    console.error('[Notifications] Failed to check upcoming tasks:', error)
  }
}

// Combined check for all maintenance notifications
export const checkMaintenanceNotifications = async (): Promise<void> => {
  await checkOverdueTasks()
  // Delay between notifications to avoid overwhelming
  setTimeout(async () => {
    await checkUpcomingTasks()
  }, 2000)
}

// Start periodic notification checks (every 30 minutes)
let notificationInterval: NodeJS.Timeout | null = null

export const startNotificationScheduler = (intervalMinutes: number = 30): void => {
  if (notificationInterval) {
    clearInterval(notificationInterval)
  }

  // Initial check after a short delay (let the app load first)
  setTimeout(() => {
    checkMaintenanceNotifications()
  }, 10000) // 10 seconds after start

  // Periodic checks
  notificationInterval = setInterval(() => {
    checkMaintenanceNotifications()
  }, intervalMinutes * 60 * 1000)

  console.log(`[Notifications] Scheduler started with ${intervalMinutes} minute interval`)
}

export const stopNotificationScheduler = (): void => {
  if (notificationInterval) {
    clearInterval(notificationInterval)
    notificationInterval = null
    console.log('[Notifications] Scheduler stopped')
  }
}

// Export for use in Electron IPC if needed
export default {
  requestNotificationPermission,
  sendNotification,
  checkOverdueTasks,
  checkUpcomingTasks,
  checkMaintenanceNotifications,
  startNotificationScheduler,
  stopNotificationScheduler,
}
