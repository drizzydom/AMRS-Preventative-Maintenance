import { lazy, Suspense, useEffect, useState } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import TitleBar from './components/TitleBar'
import MenuBar from './components/MenuBar'
import Sidebar from './components/Sidebar'
import OnboardingTour from './components/onboarding/OnboardingTour'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import PermissionGate from './components/auth/PermissionGate'
import ErrorBoundary from './components/ErrorBoundary'
import { initializeSocket, disconnectSocket } from './utils/socket'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { 
  requestNotificationPermission, 
  startNotificationScheduler, 
  stopNotificationScheduler 
} from './services/notificationService'
import './styles/App.css'

const { Content } = Layout

// Lazy load pages for better performance
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Machines = lazy(() => import('./pages/Machines'))
const Maintenance = lazy(() => import('./pages/Maintenance'))
const MaintenanceRecords = lazy(() => import('./pages/MaintenanceRecords'))
const Audits = lazy(() => import('./pages/Audits'))
const Sites = lazy(() => import('./pages/Sites'))
const Users = lazy(() => import('./pages/admin/Users'))
const Settings = lazy(() => import('./pages/Settings'))
const AdminPanel = lazy(() => import('./pages/AdminPanel'))
const ReportsPreview = lazy(() => import('./pages/reports/ReportsPreview'))
const AuditReportsPreview = lazy(() => import('./pages/reports/AuditReportsPreview'))
const MaintenanceReportView = lazy(() => import('./pages/reports/MaintenanceReportView'))
const AuditReportView = lazy(() => import('./pages/reports/AuditReportView'))

// Loading component for lazy loaded pages
const PageLoader = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100%',
    minHeight: '400px'
  }}>
    <Spin size="large" tip="Loading..." />
  </div>
)

function App() {
  // Initialize Socket.IO connection when app mounts
  useEffect(() => {
    console.log('[App] Initializing Socket.IO connection')
    const socket = initializeSocket()

    // Cleanup on unmount
    return () => {
      console.log('[App] Disconnecting Socket.IO')
      disconnectSocket()
    }
  }, [])

  return (
    <AuthProvider>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public route - Login page without sidebar/menubar */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes with app layout */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}

// Separate component for app layout to use hooks (useNavigate for IPC handlers)
function AppLayout() {
  const navigate = useNavigate()
  const [showOnboarding, setShowOnboarding] = useState(false)

  // Initialize keyboard shortcuts
  useKeyboardShortcuts()

  // Check for first-time user
  useEffect(() => {
    const onboardingComplete = localStorage.getItem('amrs_onboarding_complete')
    if (!onboardingComplete) {
      // Small delay to let the app render first
      const timer = setTimeout(() => {
        setShowOnboarding(true)
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [])

  // Initialize desktop notifications
  useEffect(() => {
    const initNotifications = async () => {
      const hasPermission = await requestNotificationPermission()
      if (hasPermission) {
        console.log('[App] Notification permission granted, starting scheduler')
        startNotificationScheduler(30) // Check every 30 minutes
      } else {
        console.log('[App] Notification permission not granted')
      }
    }

    initNotifications()

    return () => {
      stopNotificationScheduler()
    }
  }, [])

  // Handle Electron IPC messages for native menu actions
  useEffect(() => {
    // Check if running in Electron
    const isElectron = window.navigator.userAgent.toLowerCase().includes('electron')
    
    if (isElectron && (window as any).electron?.ipcRenderer) {
      const { ipcRenderer } = (window as any).electron

      // Navigation events from menu
      ipcRenderer.on('menu-navigate', (_event: any, path: string) => {
        console.log('[IPC] Menu navigate to:', path)
        navigate(path)
      })

      // New maintenance record action
      ipcRenderer.on('menu-new-maintenance', () => {
        console.log('[IPC] New maintenance triggered')
        navigate('/maintenance')
      })

      // Print action
      ipcRenderer.on('menu-print', () => {
        console.log('[IPC] Print triggered')
        window.print()
      })

      // About dialog (could open modal)
      ipcRenderer.on('menu-about', () => {
        console.log('[IPC] About triggered')
        // Could show about modal here
      })

      // Cleanup listeners on unmount
      return () => {
        ipcRenderer.removeAllListeners('menu-navigate')
        ipcRenderer.removeAllListeners('menu-new-maintenance')
        ipcRenderer.removeAllListeners('menu-print')
        ipcRenderer.removeAllListeners('menu-about')
      }
    }
  }, [navigate])

  return (
    <Layout className="app-layout">
      <TitleBar />
      <MenuBar />
      <Layout hasSider>
        <Sidebar />
        <Layout className="content-layout">
          <Content className="app-content">
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/machines" element={<Machines />} />
              <Route path="/maintenance" element={<Maintenance />} />
              <Route
                path="/maintenance-records"
                element={(
                  <PermissionGate requiredPermissions={['maintenance.view']}>
                    <MaintenanceRecords />
                  </PermissionGate>
                )}
              />
              <Route path="/audits" element={<Audits />} />
              <Route path="/sites" element={<Sites />} />
              <Route
                path="/users"
                element={(
                  <PermissionGate requireAdmin>
                    <Users />
                  </PermissionGate>
                )}
              />
              <Route
                path="/admin"
                element={(
                  <PermissionGate requireAdmin>
                    <AdminPanel />
                  </PermissionGate>
                )}
              />
              <Route path="/settings" element={<Settings />} />
              <Route
                path="/reports"
                element={(
                  <PermissionGate requiredPermissions={['reports.view']}>
                    <ErrorBoundary>
                      <ReportsPreview />
                    </ErrorBoundary>
                  </PermissionGate>
                )}
              />
              <Route
                path="/reports/maintenance/view"
                element={(
                  <PermissionGate requiredPermissions={['reports.view']}>
                    <ErrorBoundary>
                      <MaintenanceReportView />
                    </ErrorBoundary>
                  </PermissionGate>
                )}
              />
              <Route
                path="/reports/audits"
                element={(
                  <PermissionGate requiredPermissions={['reports.view', 'audits.view']}>
                    <ErrorBoundary>
                      <AuditReportsPreview />
                    </ErrorBoundary>
                  </PermissionGate>
                )}
              />
              <Route
                path="/reports/audits/view"
                element={(
                  <PermissionGate requiredPermissions={['reports.view', 'audits.view']}>
                    <ErrorBoundary>
                      <AuditReportView />
                    </ErrorBoundary>
                  </PermissionGate>
                )}
              />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>

      {/* Onboarding Tour for first-time users */}
      <OnboardingTour
        open={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onComplete={() => {
          console.log('[App] Onboarding tour completed')
        }}
      />
    </Layout>
  )
}

export default App
