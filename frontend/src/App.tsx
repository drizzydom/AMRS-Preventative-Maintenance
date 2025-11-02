import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import TitleBar from './components/TitleBar'
import MenuBar from './components/MenuBar'
import Sidebar from './components/Sidebar'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import './styles/App.css'

const { Content } = Layout

// Lazy load pages for better performance
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Machines = lazy(() => import('./pages/Machines'))
const Maintenance = lazy(() => import('./pages/Maintenance'))
const Audits = lazy(() => import('./pages/Audits'))
const Sites = lazy(() => import('./pages/Sites'))
const Users = lazy(() => import('./pages/admin/Users'))
const Settings = lazy(() => import('./pages/Settings'))
const ReportsPreview = lazy(() => import('./pages/reports/ReportsPreview'))
const AuditReportsPreview = lazy(() => import('./pages/reports/AuditReportsPreview'))

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
  return (
    <AuthProvider>
      <Layout className="app-layout">
        <TitleBar />
        <MenuBar />
        <Layout hasSider>
          <Sidebar />
          <Layout className="content-layout">
            <Content className="app-content">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route
                    path="/dashboard"
                    element={
                      <ProtectedRoute>
                        <Dashboard />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/machines"
                    element={
                      <ProtectedRoute>
                        <Machines />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/maintenance"
                    element={
                      <ProtectedRoute>
                        <Maintenance />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/audits"
                    element={
                      <ProtectedRoute>
                        <Audits />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/sites"
                    element={
                      <ProtectedRoute>
                        <Sites />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/users"
                    element={
                      <ProtectedRoute>
                        <Users />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/settings"
                    element={
                      <ProtectedRoute>
                        <Settings />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/reports"
                    element={
                      <ProtectedRoute>
                        <ReportsPreview />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/reports/audits"
                    element={
                      <ProtectedRoute>
                        <AuditReportsPreview />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="/" element={<Navigate to="/login" replace />} />
                </Routes>
              </Suspense>
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </AuthProvider>
  )
}

export default App
